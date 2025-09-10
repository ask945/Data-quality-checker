import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def calculate_anomaly_scores(anomaly_results: Dict[str, pd.DataFrame], predictions: np.ndarray = None) -> pd.DataFrame:
    all_scores = []
    
    for method, results in anomaly_results.items():
        if isinstance(results, pd.DataFrame) and not results.empty:
            for _, row in results.iterrows():
                score = {
                    'row_index': row['row_index'] if 'row_index' in row else row.name,
                    'method': method,
                    'issue_type': row.get('issue_type', method),
                    'confidence': row.get('anomaly_score', 1.0) if 'anomaly_score' in row else 1.0,
                    'value': row.get('value', 'N/A')
                }
                all_scores.append(score)
    
    return pd.DataFrame(all_scores)

def set_anomaly_thresholds(method: str) -> float:
    thresholds = {
        'numeric_outlier': 0.7,
        'rare_category': 0.8,
        'complex_pattern_anomaly': 0.5,
        'duplicate_record': 1.0,
        'missing_required_field': 0.9,
        'invalid_foreign_key': 0.8,
        'potential_orphaned_record': 0.6,
        'referential_integrity_violation': 0.9,
        'potential_accidental_deletion': 0.7,
        'inconsistent_update': 0.8,
        'partial_update': 0.7,
        'data_type_violation': 0.9
    }
    return thresholds.get(method, 0.5)

def filter_high_confidence_anomalies(scores_df: pd.DataFrame, min_confidence: float = 0.5) -> pd.DataFrame:
    return scores_df[scores_df['confidence'] >= min_confidence]

def get_anomaly_summary(scores_df: pd.DataFrame) -> Dict:
    if scores_df.empty:
        return {
            'total_anomalies': 0,
            'methods_used': [],
            'confidence_range': (0, 0),
            'top_issues': []
        }
    # Exclude feature_importance rows from summary
    filtered_df = scores_df[scores_df['issue_type'] != 'feature_importance']
    if filtered_df.empty:
        return {
            'total_anomalies': 0,
            'methods_used': [],
            'confidence_range': (0, 0),
            'top_issues': []
        }
    summary = {
        'total_anomalies': len(filtered_df),
        'methods_used': filtered_df['method'].unique().tolist(),
        'confidence_range': (filtered_df['confidence'].min(), filtered_df['confidence'].max()),
        'top_issues': filtered_df['issue_type'].value_counts().head(5).to_dict()
    }
    return summary

def rank_anomalies_by_severity(scores_df: pd.DataFrame) -> pd.DataFrame:
    if scores_df.empty:
        return scores_df
    
    method_weights = {
        'complex_pattern_anomaly': 1.0,
        'numeric_outlier': 0.8,
        'rare_category': 0.6,
        'duplicate_record': 1.0,
        'missing_required_field': 0.9,
        'invalid_foreign_key': 0.8,
        'potential_orphaned_record': 0.7,
        'referential_integrity_violation': 1.0,
        'potential_accidental_deletion': 0.7,
        'inconsistent_update': 0.9,
        'partial_update': 0.7,
        'data_type_violation': 0.9
    }
    
    scores_df['method_weight'] = scores_df['method'].map(method_weights).fillna(0.5)
    scores_df['severity_score'] = scores_df['confidence'] * scores_df['method_weight']
    return scores_df.sort_values('severity_score', ascending=False) 