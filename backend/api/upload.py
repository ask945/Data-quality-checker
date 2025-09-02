import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd
import io
import re
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from ml.anomaly_checker import run_comprehensive_anomaly_detection
from sqlalchemy import create_engine
import random
import numpy as np
import math

router = APIRouter()

# Global in-memory cache for uploaded tables
in_memory_tables = {}

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
    """Process a single uploaded file and return its analysis results"""
    filename = file.filename
    ext = os.path.splitext(filename)[-1].lower()
    
    try:
        # Reset file pointer to beginning
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
    
    # Generate unique table name with timestamp to avoid conflicts
    base_name = os.path.splitext(os.path.basename(filename))[0].replace("-", "_").replace(" ", "_").lower()
    table_name = f"{base_name}_{hash(filename) % 10000}"
    
    # Store in memory
    in_memory_tables[table_name] = df
    
    schema = df.dtypes.apply(lambda x: str(x)).to_dict()
    sample = df.head(10).where(pd.notnull(df.head(10)), None).to_dict(orient="records")

    # Run anomaly checker based on analysis_type
    print(f"🔍 Running anomaly detection for {filename} in mode: {analysis_type}")
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
    """Recursively convert NaN/Inf and numpy/pandas types to JSON-safe Python types."""
    # Handle numpy scalar types
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        obj = obj.item()
    # Handle floats with NaN/Inf
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    # Handle dictionaries
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    # Handle iterables
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    # Handle pandas objects
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
    analysis_type: str = Query("sql", enum=["sql", "ml"])
):
    """Multiple files upload endpoint"""
    random.seed(42)
    np.random.seed(42)
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    errors = []
    
    for file in files:
        try:
            result = process_single_file(file, analysis_type)
            results.append(result)
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
    
    return JSONResponse(sanitize_for_json(response_data))

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

    # Run anomaly checker based on analysis_type
    print(f"🔍 Running anomaly detection for table {table_name} in mode: {analysis_type}")
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
    """Get list of all uploaded tables in memory"""
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
    """Delete a specific table from memory"""
    if table_name in in_memory_tables:
        del in_memory_tables[table_name]
        return JSONResponse({"message": f"Table '{table_name}' deleted successfully"})
    else:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

@router.delete("/tables")
def clear_all_tables():
    """Clear all tables from memory"""
    cleared_count = len(in_memory_tables)
    in_memory_tables.clear()
    return JSONResponse({"message": f"Cleared {cleared_count} tables from memory"})