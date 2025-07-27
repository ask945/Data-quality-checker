import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql.data_fetcher import conn
import pandas as pd
from ml.anomaly_ensemble import run_all_anomaly_detectors, combine_anomaly_results, generate_anomaly_report, get_anomaly_recommendations
import numpy as np
import re

def run_comprehensive_anomaly_detection(df: pd.DataFrame = None, contamination: float = 0.1):
    import io
    import sys
    log_stream = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = log_stream
    try:
        if df is None:
            df = pd.read_sql("SELECT * FROM customers LIMIT 1000", conn)
        # Replace all string 'NULL' (case-insensitive) with np.nan for compatibility
        def null_to_nan(val):
            if isinstance(val, str) and re.fullmatch(r'null', val, re.IGNORECASE):
                return np.nan
            return val
        df = df.applymap(null_to_nan)
        print("🔍 Starting comprehensive anomaly detection...")
        print(f"📊 Dataset: {len(df)} rows, {len(df.columns)} columns")
        all_results = run_all_anomaly_detectors(df, contamination)
        combined_results = combine_anomaly_results(all_results)
        report = generate_anomaly_report(df, combined_results, all_results.get('feature_importance'))
        recommendations = get_anomaly_recommendations(report)
        # combined_results.to_csv("output/flagged_anomalies.csv", index=False)  # Removed file saving
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
    results = run_comprehensive_anomaly_detection()
    report = results['report']
    recommendations = results['recommendations']
    log_output = results.get('log', '')
    # Build formatted output as in the backend API
    formatted_output = f"{log_output}\n\nTop Anomalies\n{report.get('top_anomalies', [])}\n\nRECOMMENDATIONS:\n  " + "\n  ".join(recommendations)
    print(formatted_output)
    
    if not results['anomaly_results'].empty:
        print("\n🚨 TOP ANOMALIES:")
        print(results['anomaly_results'].head(5))
        # Save only actual anomaly events (exclude feature_importance) to output/detailed_anomaly_report.csv
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        os.makedirs(output_dir, exist_ok=True)
        detailed_report_path = os.path.join(output_dir, 'detailed_anomaly_report.csv')
        filtered_anomalies = results['anomaly_results'][results['anomaly_results']['issue_type'] != 'feature_importance']
        filtered_anomalies.to_csv(detailed_report_path, index=False)
        print(f"\n📁 Detailed anomaly report saved to: {detailed_report_path}")
    
    if results['all_results'].get('feature_importance') is not None and not results['all_results']['feature_importance'].empty:
        print("\n🎯 TOP FEATURES CONTRIBUTING TO ANOMALIES:")
        print(results['all_results']['feature_importance'].head(5))
