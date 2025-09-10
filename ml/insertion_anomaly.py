import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def detect_duplicate_records(df: pd.DataFrame, subset: List[str] = None) -> pd.DataFrame:
    results = []
    if subset is None:
        subset = df.columns.tolist()
    duplicates = df.duplicated(subset=subset, keep=False)
    duplicate_indices = df[duplicates].index.tolist()
    
    for idx in duplicate_indices:
        results.append({
            'row_index': idx,
            'issue_type': 'duplicate_record',
            'confidence': 1.0,
            'value': 'Duplicate data',
            'details': f"Duplicate found in columns: {', '.join(subset)}"
        })
    
    return pd.DataFrame(results)

def detect_missing_required_fields(df: pd.DataFrame, required_columns: List[str] = None) -> pd.DataFrame:
    results = []
    if required_columns is None:
        null_percentages = df.isnull().mean()
        required_columns = null_percentages[null_percentages < 0.1].index.tolist()
    
    for col in required_columns:
        if col in df.columns:
            missing_indices = df[df[col].isnull()].index.tolist()
            
            for idx in missing_indices:
                results.append({
                    'row_index': idx,
                    'issue_type': 'missing_required_field',
                    'confidence': 0.9,
                    'value': f"NULL in {col}",
                    'details': f"Required field '{col}' is missing"
                })
    
    return pd.DataFrame(results)

def detect_invalid_foreign_keys(df: pd.DataFrame, foreign_key_mappings: Dict[str, str] = None) -> pd.DataFrame:
    results = []
    if foreign_key_mappings is None:
        potential_fks = [col for col in df.columns if col.endswith('_id') or col.endswith('Id')]
        foreign_key_mappings = {fk: fk for fk in potential_fks}
    
    for fk_col, referenced_table in foreign_key_mappings.items():
        if fk_col in df.columns:
            fk_values = df[fk_col].dropna().unique()
            for idx, value in df[fk_col].items():
                if pd.notna(value):
                    if isinstance(value, (int, float)):
                        if value < 0:
                            results.append({
                                'row_index': idx,
                                'issue_type': 'invalid_foreign_key',
                                'confidence': 0.8,
                                'value': f"{fk_col}: {value}",
                                'details': f"Negative foreign key value in {fk_col}"
                            })
                        elif value > 999999999:
                            results.append({
                                'row_index': idx,
                                'issue_type': 'invalid_foreign_key',
                                'confidence': 0.6,
                                'value': f"{fk_col}: {value}",
                                'details': f"Suspiciously large foreign key value in {fk_col}"
                            })
                    else:
                        results.append({
                            'row_index': idx,
                            'issue_type': 'invalid_foreign_key',
                            'confidence': 0.7,
                            'value': f"{fk_col}: {value}",
                            'details': f"Non-numeric foreign key value in {fk_col}"
                        })
    
    return pd.DataFrame(results)

def detect_insertion_anomalies(df: pd.DataFrame, required_columns: List[str] = None, 
                             foreign_key_mappings: Dict[str, str] = None) -> pd.DataFrame:
    all_results = []
    try:
        duplicate_results = detect_duplicate_records(df)
        all_results.append(duplicate_results)
        print(f"✓ Duplicate records detected: {len(duplicate_results)}")
    except Exception as e:
        print(f"✗ Duplicate detection failed: {e}")
    try:
        missing_results = detect_missing_required_fields(df, required_columns)
        all_results.append(missing_results)
        print(f"✓ Missing required fields detected: {len(missing_results)}")
    except Exception as e:
        print(f"✗ Missing field detection failed: {e}")
    try:
        fk_results = detect_invalid_foreign_keys(df, foreign_key_mappings)
        all_results.append(fk_results)
        print(f"✓ Invalid foreign keys detected: {len(fk_results)}")
    except Exception as e:
        print(f"✗ Foreign key validation failed: {e}")
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        return combined_results
    else:
        return pd.DataFrame() 