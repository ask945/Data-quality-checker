import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
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

router = APIRouter()

# PostgreSQL connection parameters
DB_PARAMS = {
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "user": "postgres",
    "password": "Askssk1@"
}

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

@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    # Set random seeds for reproducibility on every request
    random.seed(42)
    np.random.seed(42)
    filename = file.filename
    ext = os.path.splitext(filename)[-1].lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(file.file)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file.file)
        elif ext == ".json":
            df = pd.read_json(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing error: {e}")

    df = sanitize_columns(df)
    # Replace all string 'NULL' (case-insensitive) with np.nan for compatibility
    def null_to_nan(val):
        if isinstance(val, str) and re.fullmatch(r'null', val, re.IGNORECASE):
            return np.nan
        return val
    df = df.applymap(null_to_nan)
    table_name = os.path.splitext(os.path.basename(filename))[0].replace("-", "_").replace(" ", "_").lower()

    # Store DataFrame in global in-memory cache
    in_memory_tables[table_name] = df

    schema = df.dtypes.apply(lambda x: str(x)).to_dict()
    sample = df.head(10).where(pd.notnull(df.head(10)), None).to_dict(orient="records")

    # Run anomaly checker (in memory, no file saving)
    results = run_comprehensive_anomaly_detection(df)
    report = results['report']
    recommendations = results['recommendations']
    log_output = results.get('log', '')

    # Build JSON-serializable response
    formatted_output = (
        f"{log_output}\n\n"
        f"Total anomalies found (events): {report.get('anomaly_event_count', 'N/A')}\n"
        f"Unique rows flagged: {report.get('unique_rows_flagged', 'N/A')}\n"
        f"Anomaly breakdown by method: {report.get('method_breakdown', {})}\n"
        f"RECOMMENDATIONS:\n  " + "\n  ".join(recommendations)
    )
    response = {
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
        "formatted_output": formatted_output
    }
    return JSONResponse(response)

@router.get("/analyze/{table_name}")
def analyze_table(table_name: str):
    # Set random seeds for reproducibility on every request
    random.seed(42)
    np.random.seed(42)
    # Look up DataFrame in global in-memory cache
    df = in_memory_tables.get(table_name)
    if df is None:
        return JSONResponse(status_code=404, content={"detail": f"Table '{table_name}' not found in memory. Please upload it first."})

    df = sanitize_columns(df)
    # Replace all string 'NULL' (case-insensitive) with np.nan for compatibility
    def null_to_nan(val):
        if isinstance(val, str) and re.fullmatch(r'null', val, re.IGNORECASE):
            return np.nan
        return val
    df = df.applymap(null_to_nan)
    schema = df.dtypes.apply(lambda x: str(x)).to_dict()
    sample = df.head(10).where(pd.notnull(df.head(10)), None).to_dict(orient="records")

    # Run anomaly checker (in memory, no file saving)
    results = run_comprehensive_anomaly_detection(df)
    report = results['report']
    recommendations = results['recommendations']
    log_output = results.get('log', '')

    # Build JSON-serializable response
    formatted_output = (
        f"{log_output}\n\n"
        f"Total anomalies found (events): {report.get('anomaly_event_count', 'N/A')}\n"
        f"Unique rows flagged: {report.get('unique_rows_flagged', 'N/A')}\n"
        f"Anomaly breakdown by method: {report.get('method_breakdown', {})}\n"
        f"RECOMMENDATIONS:\n  " + "\n  ".join(recommendations)
    )
    response = {
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
        "formatted_output": formatted_output
    }
    return JSONResponse(response) 