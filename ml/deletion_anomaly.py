import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def detect_orphaned_records(df: pd.DataFrame, parent_child_mappings: Dict[str, str] = None) -> pd.DataFrame:
    results = []
    if parent_child_mappings is None:
        potential_fks = [col for col in df.columns if col.endswith('_id') or col.endswith('Id')]
        parent_child_mappings = {fk: fk for fk in potential_fks}
    
    for child_col, parent_ref in parent_child_mappings.items():
        if child_col in df.columns:
            fk_values = df[child_col].dropna().unique()
            for idx, value in df[child_col].items():
                if pd.notna(value):
                    if isinstance(value, (int, float)):
                        value_count = (df[child_col] == value).sum()
                        if value_count == 1 and value > 1000:
                            results.append({
                                'row_index': idx,
                                'issue_type': 'potential_orphaned_record',
                                'confidence': 0.6,
                                'value': f"{child_col}: {value}",
                                'details': f"Potential orphaned record - {child_col} value {value} appears only once"
                            })
    
    return pd.DataFrame(results)

def detect_referential_integrity_violations(df: pd.DataFrame, 
                                         constraint_mappings: Dict[str, Dict] = None) -> pd.DataFrame:
    results = []
    if constraint_mappings is None:
        constraint_mappings = {}
        for col in df.columns:
            if col.endswith('_id') or col.endswith('Id'):
                constraint_mappings[col] = {
                    'type': 'foreign_key',
                    'min_value': 1,
                    'max_value': 999999999
                }
    
    for col, constraints in constraint_mappings.items():
        if col in df.columns:
            for idx, value in df[col].items():
                if pd.notna(value):
                    if 'min_value' in constraints and value < constraints['min_value']:
                        results.append({
                            'row_index': idx,
                            'issue_type': 'referential_integrity_violation',
                            'confidence': 0.9,
                            'value': f"{col}: {value}",
                            'details': f"Value {value} below minimum {constraints['min_value']} for {col}"
                        })
                    
                    if 'max_value' in constraints and value > constraints['max_value']:
                        results.append({
                            'row_index': idx,
                            'issue_type': 'referential_integrity_violation',
                            'confidence': 0.8,
                            'value': f"{col}: {value}",
                            'details': f"Value {value} above maximum {constraints['max_value']} for {col}"
                        })
    
    return pd.DataFrame(results)

def detect_accidental_deletions(df: pd.DataFrame, critical_columns: List[str] = None) -> pd.DataFrame:
    results = []
    if critical_columns is None:
        null_percentages = df.isnull().mean()
        unique_ratios = df.nunique() / len(df)
        critical_columns = []
        
        for col in df.columns:
            if null_percentages[col] < 0.05 and unique_ratios[col] > 0.8:
                critical_columns.append(col)
    
    for col in critical_columns:
        if col in df.columns:
            null_mask = df[col].isnull()
            consecutive_nulls = null_mask.astype(int).groupby(
                (null_mask != null_mask.shift()).cumsum()
            ).sum()
            
            if consecutive_nulls.max() > 5:
                null_indices = df[null_mask].index.tolist()
                for idx in null_indices[:10]:
                    results.append({
                        'row_index': idx,
                        'issue_type': 'potential_accidental_deletion',
                        'confidence': 0.7,
                        'value': f"NULL in {col}",
                        'details': f"Potential accidental deletion detected in {col}"
                    })
    
    return pd.DataFrame(results)

def detect_deletion_anomalies(df: pd.DataFrame, parent_child_mappings: Dict[str, str] = None,
                            constraint_mappings: Dict[str, Dict] = None,
                            critical_columns: List[str] = None) -> pd.DataFrame:
    all_results = []
    try:
        orphaned_results = detect_orphaned_records(df, parent_child_mappings)
        all_results.append(orphaned_results)
        print(f"✓ Orphaned records detected: {len(orphaned_results)}")
    except Exception as e:
        print(f"✗ Orphaned record detection failed: {e}")
    try:
        integrity_results = detect_referential_integrity_violations(df, constraint_mappings)
        all_results.append(integrity_results)
        print(f"✓ Referential integrity violations detected: {len(integrity_results)}")
    except Exception as e:
        print(f"✗ Integrity violation detection failed: {e}")
    try:
        accidental_results = detect_accidental_deletions(df, critical_columns)
        all_results.append(accidental_results)
        print(f"✓ Potential accidental deletions detected: {len(accidental_results)}")
    except Exception as e:
        print(f"✗ Accidental deletion detection failed: {e}")
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        return combined_results
    else:
        return pd.DataFrame() 