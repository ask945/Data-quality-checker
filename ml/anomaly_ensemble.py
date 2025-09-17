import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ml.numeric_anomaly import detect_numeric_anomalies
from ml.categorical_anomaly import detect_categorical_anomalies
from ml.lightgbm_anomaly import train_lightgbm_anomaly_detector, detect_lightgbm_anomalies, get_feature_importance
from ml.insertion_anomaly import detect_insertion_anomalies
from ml.deletion_anomaly import detect_deletion_anomalies
from ml.update_anomaly import detect_update_anomalies
from ml.anomaly_scorer import calculate_anomaly_scores, filter_high_confidence_anomalies, get_anomaly_summary, rank_anomalies_by_severity

def run_all_anomaly_detectors(df: pd.DataFrame, contamination: float = 0.05, mode: str = "sql") -> Dict:
    results = {}

    if mode in ("sql", "ml"):
        try:
            numeric_results = detect_numeric_anomalies(df)
            results['numeric'] = numeric_results
            print(f"✓ Numeric anomalies detected: {len(numeric_results)}")
        except Exception as e:
            print(f"✗ Numeric anomaly detection failed: {e}")
            results['numeric'] = pd.DataFrame()

        try:
            categorical_results = detect_categorical_anomalies(df)
            results['categorical'] = categorical_results
            print(f"✓ Categorical anomalies detected: {len(categorical_results)}")
        except Exception as e:
            print(f"✗ Categorical anomaly detection failed: {e}")
            results['categorical'] = pd.DataFrame()

        try:
            model, label_encoders = train_lightgbm_anomaly_detector(df, contamination)
            lightgbm_results, predictions = detect_lightgbm_anomalies(df, model, label_encoders)
            feature_importance = get_feature_importance(model, df)
            results['lightgbm'] = lightgbm_results
            results['lightgbm_predictions'] = predictions
            results['feature_importance'] = feature_importance
            print(f"✓ Complex pattern anomalies detected: {len(lightgbm_results)}")
        except Exception as e:
            print(f"✗ LightGBM anomaly detection failed: {e}")
            results['lightgbm'] = pd.DataFrame()
            results['lightgbm_predictions'] = None
            results['feature_importance'] = pd.DataFrame()

    if mode == "sql":

        try:
            insertion_results = detect_insertion_anomalies(df)
            results['insertion'] = insertion_results
            print(f"✓ Insertion anomalies detected: {len(insertion_results)}")
        except Exception as e:
            print(f"✗ Insertion anomaly detection failed: {e}")
            results['insertion'] = pd.DataFrame()

        try:
            deletion_results = detect_deletion_anomalies(df)
            results['deletion'] = deletion_results
            print(f"✓ Deletion anomalies detected: {len(deletion_results)}")
        except Exception as e:
            print(f"✗ Deletion anomaly detection failed: {e}")
            results['deletion'] = pd.DataFrame()

        try:
            update_results = detect_update_anomalies(df)
            results['update'] = update_results
            print(f"✓ Update anomalies detected: {len(update_results)}")
        except Exception as e:
            print(f"✗ Update anomaly detection failed: {e}")
            results['update'] = pd.DataFrame()
    

    return results



def combine_anomaly_results(all_results: Dict) -> pd.DataFrame:
    
    scores_df = calculate_anomaly_scores(
        all_results, 
        predictions=all_results.get('lightgbm_predictions')
    )

    filtered_scores = filter_high_confidence_anomalies(scores_df, min_confidence=0.3)
    ranked_scores = rank_anomalies_by_severity(filtered_scores)
    return ranked_scores

def generate_anomaly_report(df: pd.DataFrame, anomaly_results: pd.DataFrame, feature_importance: pd.DataFrame = None) -> Dict:
    filtered_anomaly_results = anomaly_results[anomaly_results['issue_type'] != 'feature_importance'] if not anomaly_results.empty else anomaly_results
    summary = get_anomaly_summary(filtered_anomaly_results)
    total_rows = len(df)
    anomaly_percentage = (summary['total_anomalies'] / total_rows) * 100 if total_rows > 0 else 0
    quality_score = max(0, 100 - anomaly_percentage)
    unique_rows_flagged = filtered_anomaly_results['row_index'].nunique() if not filtered_anomaly_results.empty and 'row_index' in filtered_anomaly_results else 0
    method_breakdown = filtered_anomaly_results['method'].value_counts().to_dict() if not filtered_anomaly_results.empty and 'method' in filtered_anomaly_results else {}
    report = {
        'dataset_info': {
            'total_rows': total_rows,
            'total_columns': len(df.columns),
            'data_types': df.dtypes.value_counts().to_dict()
        },
        'anomaly_summary': summary,
        'quality_metrics': {
            'anomaly_percentage': round(anomaly_percentage, 2),
            'quality_score': round(quality_score, 2),
            'confidence_range': summary['confidence_range']
        },
        'top_anomalies': filtered_anomaly_results.head(10).to_dict('records') if not filtered_anomaly_results.empty else [],
        'feature_importance': feature_importance.head(10).to_dict('records') if feature_importance is not None and not feature_importance.empty else [],
        'unique_rows_flagged': unique_rows_flagged,
        'anomaly_event_count': len(filtered_anomaly_results),
        'method_breakdown': method_breakdown
    }
    return report

def get_anomaly_recommendations(report: Dict) -> List[str]:
    
    recommendations = []
    
    quality_score = report['quality_metrics']['quality_score']
    if quality_score < 50:
        recommendations.append("⚠️ Critical: Data quality is very poor. Immediate data cleaning required.")
    elif quality_score < 80:
        recommendations.append("⚠️ Warning: Data quality needs improvement. Consider data cleaning.")
    else:
        recommendations.append("✅ Good: Data quality is acceptable.")

    methods_used = report['anomaly_summary']['methods_used']
    if 'numeric' in methods_used:
        recommendations.append("📊 Numeric outliers detected. Review extreme values in numeric columns.")
    
    if 'categorical' in methods_used:
        recommendations.append("🏷️ Rare categories found. Check for typos or inconsistent categories.")
    
    if 'lightgbm' in methods_used:
        recommendations.append("🤖 Complex pattern anomalies detected. Review unusual combinations of values across columns.")
    
    if 'insertion' in methods_used:
        recommendations.append("➕ Insertion anomalies detected. Check for duplicate records, missing required fields, or invalid foreign keys.")

    if 'deletion' in methods_used:
        recommendations.append("➖ Deletion anomalies detected. Review orphaned records or referential integrity violations.")

    if 'update' in methods_used:
        recommendations.append("✏️ Update anomalies detected. Look for inconsistent updates, partial updates, or data type violations.")

    if report['feature_importance']:
        top_feature = report['feature_importance'][0]['feature']
        recommendations.append(f"🎯 Focus on column '{top_feature}' - it contributes most to anomalies.")
    
    return recommendations