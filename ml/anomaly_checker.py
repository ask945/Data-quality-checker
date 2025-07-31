import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from ml.anomaly_ensemble import run_all_anomaly_detectors, combine_anomaly_results, generate_anomaly_report, get_anomaly_recommendations
import numpy as np
import re

def run_comprehensive_anomaly_detection(df: pd.DataFrame, contamination: float = 0.1,mode:str="sql"):
    import io
    import sys
    log_stream = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = log_stream
    try:
        # Replace all string 'NULL' (case-insensitive) with np.nan for compatibility
        def null_to_nan(val):
            if isinstance(val, str) and re.fullmatch(r'null', val, re.IGNORECASE):
                return np.nan
            return val
        df = df.applymap(null_to_nan)
        print("🔍 Starting comprehensive anomaly detection...")
        print(f"📊 Dataset: {len(df)} rows, {len(df.columns)} columns")
        all_results = run_all_anomaly_detectors(df, contamination,mode)
        combined_results = combine_anomaly_results(all_results)
        report = generate_anomaly_report(df, combined_results, all_results.get('feature_importance'))
        recommendations = get_anomaly_recommendations(report)
        print("\n📋 ANOMALY DETECTION SUMMARY:")
        print(f"Total anomalies found (events): {report['anomaly_event_count']}")
        print(f"Unique rows flagged: {report['unique_rows_flagged']}")
        print(f"Anomaly breakdown by method: {report['method_breakdown']}")
        print(f"Data quality score: {report['quality_metrics']['quality_score']}%")
        print(f"Methods used: {', '.join(report['anomaly_summary']['methods_used'])}")
        log_output = log_stream.getvalue()
    finally:
        sys.stdout = old_stdout
    return {
        'dataframe': df,
        'anomaly_results': combined_results,
        'report': report,
        'recommendations': recommendations,
        'all_results': all_results,
        'log': log_output
    }

if __name__ == "__main__":
    print("⚠️ Please call `run_comprehensive_anomaly_detection(df)` with a DataFrame as input.")
