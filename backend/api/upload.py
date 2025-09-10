import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form, Body
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd
import re
from ml.anomaly_checker import run_comprehensive_anomaly_detection
import random
import numpy as np
import math

router = APIRouter()

in_memory_tables = {}


last_filename_to_table = {}

def sanitize_columns(df):
    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', col) for col in df.columns]
    df.columns = [re.sub(r'^[^a-zA-Z_]+', '_', col) if not re.match(r'^[a-zA-Z_]', col) else col for col in df.columns]
    return df

def infer_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    elif pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "TEXT"

def process_single_file(file: UploadFile, analysis_type: str):
    filename = file.filename
    ext = os.path.splitext(filename)[-1].lower()
    
    try:
        file.file.seek(0)
        
        if ext == ".csv":
            df = pd.read_csv(file.file)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file.file)
        elif ext == ".json":
            df = pd.read_json(file.file)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        raise ValueError(f"File parsing error for {filename}: {e}")

    df = sanitize_columns(df)

    def null_to_nan(val):
        if isinstance(val, str) and re.fullmatch(r'null', val, re.IGNORECASE):
            return np.nan
        return val

    df = df.applymap(null_to_nan)
    
    
    base_name = os.path.splitext(os.path.basename(filename))[0].replace("-", "_").replace(" ", "_").lower()
    table_name = f"{base_name}_{hash(filename) % 10000}"
    
   
    in_memory_tables[table_name] = df

    try:
        global last_filename_to_table
        last_filename_to_table[filename] = table_name
    except Exception:
        pass
    
    schema = df.dtypes.apply(lambda x: str(x)).to_dict()
    sample = df.head(10).where(pd.notnull(df.head(10)), None).to_dict(orient="records")

    
    results = run_comprehensive_anomaly_detection(df, mode=analysis_type)
    report = results['report']
    recommendations = results['recommendations']
    log_output = results.get('log', '')

    formatted_output = (
        f"{log_output}\n\n"
        f"Total anomalies found (events): {report.get('anomaly_event_count', 'N/A')}\n"
        f"Unique rows flagged: {report.get('unique_rows_flagged', 'N/A')}\n"
        f"Anomaly breakdown by method: {report.get('method_breakdown', {})}\n"
        f"RECOMMENDATIONS:\n  " + "\n  ".join(recommendations)
    )

    return {
        "filename": filename,
        "table_name": table_name,
        "schema": schema,
        "sample": sample,
        "row_count": len(df),
        "anomaly_summary": report.get('anomaly_summary', {}),
        "quality_metrics": report.get('quality_metrics', {}),
        "top_anomalies": report.get('top_anomalies', []),
        "feature_importance": report.get('feature_importance', []),
        "recommendations": recommendations,
        "log": log_output,
        "formatted_output": formatted_output,
        "mode_used": analysis_type,
        "status": "success"
    }

def sanitize_for_json(obj):
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        obj = obj.item()
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
   
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, pd.Series):
        return sanitize_for_json(obj.to_dict())
    if isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict(orient="records"))
    return obj

@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    analysis_type: str = Query("sql", enum=["sql", "ml"])
):
    """Single file upload endpoint - kept for backward compatibility"""
    random.seed(42)
    np.random.seed(42)
    
    try:
        result = process_single_file(file, analysis_type)
        return JSONResponse(sanitize_for_json(result))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-multiple")
def upload_multiple_files(
    files: List[UploadFile] = File(...),
    analysis_type: str = Query("sql", enum=["sql", "ml"]),
    relationships: str | None = Form(None)
):
    random.seed(42)
    np.random.seed(42)
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    errors = []
    
    filename_to_table = {}
    for file in files:
        try:
            result = process_single_file(file, analysis_type)
            results.append(result)
            filename_to_table[file.filename] = result.get("table_name")
        except Exception as e:
            error_result = {
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            }
            errors.append(error_result)
            results.append(error_result)
    
    response_data = {
        "total_files": len(files),
        "successful_uploads": len([r for r in results if r.get("status") == "success"]),
        "failed_uploads": len(errors),
        "results": results,
        "errors": errors if errors else None
    }
   
    if relationships:
        try:
            import json
            response_data["relationships"] = json.loads(relationships)
        except Exception:
            response_data["relationships"] = {"raw": relationships}

    if filename_to_table:
        response_data["filename_to_table"] = filename_to_table

    return JSONResponse(sanitize_for_json(response_data))


def _normalize_name(name: str) -> str:
    import re
    s = name.lower()
    s = re.sub(r"[^a-z0-9]", "", s)  
    return s


def _variants(name: str) -> List[str]:
    base = _normalize_name(name)
    variants = {base}
    for suffix in ("id", "key", "no", "num", "code"):
        if base.endswith(suffix) and len(base) > len(suffix) + 1:
            variants.add(base[: -len(suffix)])
    variants.add(base + "id")
    variants.add(base + "key")
    return list(variants)


def _infer_join_keys(df_primary: pd.DataFrame, df_other: pd.DataFrame) -> List[str]:
    common = [c for c in df_primary.columns if c in df_other.columns]
    preferred = [c for c in common if c.lower() in ("id", "key") or c.endswith("_id") or c.endswith("Id")]
    if preferred or common:
        return preferred or common[:1]

    best_match = None
    for c1 in df_primary.columns:
        v1 = set(_variants(c1))
        for c2 in df_other.columns:
            v2 = set(_variants(c2))
            if v1 & v2:
                
                score = 0
                if c1.lower().endswith(("id", "Id")) or c2.lower().endswith(("id", "Id")):
                    score += 2
                if len(v1 & v2) > 0:
                    score += 1
                if best_match is None or score > best_match[0]:
                    best_match = (score, c1)
    return [best_match[1]] if best_match else []


def _check_cardinality(df_primary: pd.DataFrame, df_other: pd.DataFrame, keys: List[str], relation_type: str) -> List[dict]:
    issues = []
    if not keys:
        return issues
    key = keys[0]
    if key not in df_primary.columns or key not in df_other.columns:
        return issues

    primary_dupes = df_primary.duplicated(subset=[key], keep=False)
    other_dupes = df_other.duplicated(subset=[key], keep=False)

    if relation_type == "1:1":
        if primary_dupes.any():
            for idx in df_primary[primary_dupes].index[:50]:
                issues.append({
                    "issue_type": "cardinality_violation",
                    "details": f"1:1 requires unique '{key}' in primary; duplicate at row {int(idx)}",
                })
        if other_dupes.any():
            for idx in df_other[other_dupes].index[:50]:
                issues.append({
                    "issue_type": "cardinality_violation",
                    "details": f"1:1 requires unique '{key}' in related; duplicate at row {int(idx)}",
                })
    elif relation_type == "1:M":
        if primary_dupes.any():
            for idx in df_primary[primary_dupes].index[:50]:
                issues.append({
                    "issue_type": "cardinality_violation",
                    "details": f"1:M requires unique '{key}' in primary; duplicate at row {int(idx)}",
                })
    elif relation_type == "M:1":
        if other_dupes.any():
            for idx in df_other[other_dupes].index[:50]:
                issues.append({
                    "issue_type": "cardinality_violation",
                    "details": f"M:1 requires unique '{key}' in related; duplicate at row {int(idx)}",
                })
    return issues


def _check_referential(df_primary: pd.DataFrame, df_other: pd.DataFrame, keys: List[str]) -> List[dict]:
    issues = []
    if not keys:
        return issues
    key = keys[0]
    if key not in df_primary.columns or key not in df_other.columns:
        return issues
    primary_keys = set(df_primary[key].dropna().astype(str))
    other_keys = set(df_other[key].dropna().astype(str))

    missing_in_primary = other_keys - primary_keys
    if missing_in_primary:
        issues.append({
            "issue_type": "referential_violation",
            "details": f"{len(missing_in_primary)} keys in related not present in primary for key '{key}'",
        })

    missing_in_other = primary_keys - other_keys
    if missing_in_other:
        issues.append({
            "issue_type": "unreferenced_keys",
            "details": f"{len(missing_in_other)} keys in primary not referenced by related for key '{key}'",
        })
    return issues


def _check_conflicting_values(df_primary: pd.DataFrame, df_other: pd.DataFrame, keys: List[str]) -> List[dict]:
    issues = []
    if not keys:
        return issues
    key = keys[0]
    if key not in df_primary.columns or key not in df_other.columns:
        return issues

    overlap_cols = [c for c in df_primary.columns if c in df_other.columns and c != key]
    if not overlap_cols:
        return issues
    
    merged = df_primary[[key] + overlap_cols].merge(
        df_other[[key] + overlap_cols], on=key, how="inner", suffixes=("_primary", "_related")
    )
    for col in overlap_cols:
        left = f"{col}_primary"
        right = f"{col}_related"
        diffs = merged[(merged[left].notna()) & (merged[right].notna()) & (merged[left] != merged[right])]
        if not diffs.empty:
            issues.append({
                "issue_type": "inconsistent_update",
                "details": f"Column '{col}' has {len(diffs)} conflicting values between primary and related",
            })
    return issues


@router.post("/analyze-relationships")
def analyze_relationships(
    payload: dict = Body(..., description="Relationships and file contexts for cross-table analysis")
):
    try:
        relationships = payload.get("relationships") or {}
        file_contexts = payload.get("files") or []
      
        filename_to_table = {ctx.get("filename"): ctx.get("table_name") for ctx in file_contexts if ctx.get("filename") and ctx.get("table_name")}
        if not filename_to_table:
            filename_to_table = last_filename_to_table.copy()

        primary_idx = relationships.get("primaryIndex")
        primary_filename = relationships.get("primaryFilename")
        relations = relationships.get("relations", {})
        if primary_filename is None and isinstance(primary_idx, int) and 0 <= primary_idx < len(file_contexts):
            primary_filename = file_contexts[primary_idx].get("filename")

        if not primary_filename:
            raise HTTPException(status_code=400, detail="Primary filename not provided for relationship analysis")

        primary_table = filename_to_table.get(primary_filename)
        if not primary_table or primary_table not in in_memory_tables:
            raise HTTPException(status_code=404, detail=f"Primary table for '{primary_filename}' not found in memory")

        df_primary = in_memory_tables[primary_table]

        relation_results = []
        for related_filename, relation_type in relations.items():
            related_table = filename_to_table.get(related_filename)
            if not related_table or related_table not in in_memory_tables:
                relation_results.append({
                    "related": related_filename,
                    "relation_type": relation_type,
                    "errors": [f"Table for '{related_filename}' not found"],
                    "anomalies": []
                })
                continue

            df_other = in_memory_tables[related_table]
            keys = _infer_join_keys(df_primary, df_other)
            anomalies = []
            anomalies.extend(_check_cardinality(df_primary, df_other, keys, relation_type))
            anomalies.extend(_check_referential(df_primary, df_other, keys))
            anomalies.extend(_check_conflicting_values(df_primary, df_other, keys))

            relation_results.append({
                "related": related_filename,
                "relation_type": relation_type,
                "join_keys": keys,
                "anomalies": anomalies,
            })

        total_anomalies = sum(len(r.get("anomalies", [])) for r in relation_results)
        return JSONResponse(sanitize_for_json({
            "primary": primary_filename,
            "results": relation_results,
            "total_anomalies": total_anomalies
        }))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analyze/{table_name}")
def analyze_table(
    table_name: str,
    analysis_type: str = Query("sql", enum=["sql", "ml"])
):
    """Analyze a specific table that was previously uploaded"""
    random.seed(42)
    np.random.seed(42)

    df = in_memory_tables.get(table_name)
    if df is None:
        return JSONResponse(
            status_code=404, 
            content={"detail": f"Table '{table_name}' not found in memory. Please upload it first."}
        )

    df = sanitize_columns(df)

    def null_to_nan(val):
        if isinstance(val, str) and re.fullmatch(r'null', val, re.IGNORECASE):
            return np.nan
        return val

    df = df.applymap(null_to_nan)
    schema = df.dtypes.apply(lambda x: str(x)).to_dict()
    sample = df.head(10).where(pd.notnull(df.head(10)), None).to_dict(orient="records")
    results = run_comprehensive_anomaly_detection(df, mode=analysis_type)
    report = results['report']
    recommendations = results['recommendations']
    log_output = results.get('log', '')

    formatted_output = (
        f"{log_output}\n\n"
        f"Total anomalies found (events): {report.get('anomaly_event_count', 'N/A')}\n"
        f"Unique rows flagged: {report.get('unique_rows_flagged', 'N/A')}\n"
        f"Anomaly breakdown by method: {report.get('method_breakdown', {})}\n"
        f"RECOMMENDATIONS:\n  " + "\n  ".join(recommendations)
    )

    return JSONResponse(sanitize_for_json({
        "table_name": table_name,
        "schema": schema,
        "sample": sample,
        "row_count": len(df),
        "anomaly_summary": report.get('anomaly_summary', {}),
        "quality_metrics": report.get('quality_metrics', {}),
        "top_anomalies": report.get('top_anomalies', []),
        "feature_importance": report.get('feature_importance', []),
        "recommendations": recommendations,
        "log": log_output,
        "formatted_output": formatted_output,
        "mode_used": analysis_type
    }))

@router.get("/tables")
def list_tables():
    tables_info = []
    for table_name, df in in_memory_tables.items():
        tables_info.append({
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns)
        })
    
    return JSONResponse(sanitize_for_json({
        "total_tables": len(tables_info),
        "tables": tables_info
    }))

@router.delete("/tables/{table_name}")
def delete_table(table_name: str):
    if table_name in in_memory_tables:
        del in_memory_tables[table_name]
        return JSONResponse({"message": f"Table '{table_name}' deleted successfully"})
    else:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

@router.delete("/tables")
def clear_all_tables():
    cleared_count = len(in_memory_tables)
    in_memory_tables.clear()
    return JSONResponse({"message": f"Cleared {cleared_count} tables from memory"})