import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def detect_inconsistent_updates(df: pd.DataFrame, key_columns: List[str] = None) -> pd.DataFrame:
    """Detect inconsistent updates to the same logical record"""
    results = []
    
    # If no key columns specified, try to auto-detect
    if key_columns is None:
        # Look for columns that might be keys (ID columns, unique identifiers)
        potential_keys = []
        for col in df.columns:
            if col.endswith('_id') or col.endswith('Id') or col.endswith('_key'):
                potential_keys.append(col)
            elif df[col].nunique() / len(df) > 0.9:  # High uniqueness
                potential_keys.append(col)
        
        key_columns = potential_keys[:3]  # Use top 3 potential keys
    
    if not key_columns:
        return pd.DataFrame()
    
    # Find records with same key values but different other values
    for key_col in key_columns:
        if key_col in df.columns:
            # Group by key column and check for inconsistencies
            grouped = df.groupby(key_col)
            
            for key_value, group in grouped:
                if len(group) > 1:  # Multiple records with same key
                    # Check for inconsistencies in other columns
                    for col in df.columns:
                        if col != key_col:
                            unique_values = group[col].dropna().unique()
                            if len(unique_values) > 1:  # Inconsistent values
                                for idx in group.index:
                                    results.append({
                                        'row_index': idx,
                                        'issue_type': 'inconsistent_update',
                                        'confidence': 0.8,
                                        'value': f"{key_col}={key_value}, {col}={group.loc[idx, col]}",
                                        'details': f"Inconsistent {col} values for same {key_col}"
                                    })
    
    return pd.DataFrame(results)

def detect_partial_updates(df: pd.DataFrame, related_column_groups: List[List[str]] = None) -> pd.DataFrame:
    """Detect partial updates where some related columns are updated but others are not"""
    results = []
    
    # If no related column groups specified, auto-detect based on naming patterns
    if related_column_groups is None:
        # Group columns by common prefixes
        column_groups = {}
        for col in df.columns:
            prefix = col.split('_')[0] if '_' in col else col
            if prefix not in column_groups:
                column_groups[prefix] = []
            column_groups[prefix].append(col)
        
        # Use groups with multiple columns
        related_column_groups = [cols for cols in column_groups.values() if len(cols) > 1]
    
    for column_group in related_column_groups:
        if len(column_group) < 2:
            continue
        
        # Check for partial updates in this group
        for idx in df.index:
            row = df.loc[idx]
            
            # Count non-null values in the group
            non_null_count = sum(1 for col in column_group if pd.notna(row[col]))
            
            # If some columns have values but others don't, it might be a partial update
            if 0 < non_null_count < len(column_group):
                missing_cols = [col for col in column_group if pd.isna(row[col])]
                present_cols = [col for col in column_group if pd.notna(row[col])]
                
                results.append({
                    'row_index': idx,
                    'issue_type': 'partial_update',
                    'confidence': 0.7,
                    'value': f"Updated: {', '.join(present_cols)}, Missing: {', '.join(missing_cols)}",
                    'details': f"Partial update detected - some related columns updated, others missing"
                })
    
    return pd.DataFrame(results)

def detect_data_type_violations(df: pd.DataFrame, expected_types: Dict[str, str] = None) -> pd.DataFrame:
    """Detect data type violations in columns"""
    results = []
    
    # If no expected types specified, infer from current data
    if expected_types is None:
        expected_types = {}
        for col in df.columns:
            # Sample non-null values to infer expected type
            sample_values = df[col].dropna().head(100)
            if len(sample_values) > 0:
                # Check if numeric
                try:
                    pd.to_numeric(sample_values)
                    expected_types[col] = 'numeric'
                except:
                    # Check if date
                    try:
                        pd.to_datetime(sample_values)
                        expected_types[col] = 'datetime'
                    except:
                        expected_types[col] = 'string'
    
    for col, expected_type in expected_types.items():
        if col in df.columns:
            for idx, value in df[col].items():
                if pd.notna(value):
                    violation = False
                    
                    if expected_type == 'numeric':
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            violation = True
                    
                    elif expected_type == 'datetime':
                        try:
                            pd.to_datetime(value)
                        except (ValueError, TypeError):
                            violation = True
                    
                    elif expected_type == 'string':
                        # String type is usually flexible, but check for extreme cases
                        if isinstance(value, (int, float)) and len(str(value)) > 1000:
                            violation = True
                    
                    if violation:
                        results.append({
                            'row_index': idx,
                            'issue_type': 'data_type_violation',
                            'confidence': 0.9,
                            'value': f"{col}: {value} (type: {type(value).__name__})",
                            'details': f"Expected {expected_type} but got {type(value).__name__} in {col}"
                        })
    
    return pd.DataFrame(results)

def detect_update_anomalies(df: pd.DataFrame, key_columns: List[str] = None,
                          related_column_groups: List[List[str]] = None,
                          expected_types: Dict[str, str] = None) -> pd.DataFrame:
    """Detect all types of update anomalies"""
    
    all_results = []
    
    # 1. Detect inconsistent updates
    try:
        inconsistent_results = detect_inconsistent_updates(df, key_columns)
        all_results.append(inconsistent_results)
        print(f"✓ Inconsistent updates detected: {len(inconsistent_results)}")
    except Exception as e:
        print(f"✗ Inconsistent update detection failed: {e}")
    
    # 2. Detect partial updates
    try:
        partial_results = detect_partial_updates(df, related_column_groups)
        all_results.append(partial_results)
        print(f"✓ Partial updates detected: {len(partial_results)}")
    except Exception as e:
        print(f"✗ Partial update detection failed: {e}")
    
    # 3. Detect data type violations
    try:
        type_results = detect_data_type_violations(df, expected_types)
        all_results.append(type_results)
        print(f"✓ Data type violations detected: {len(type_results)}")
    except Exception as e:
        print(f"✗ Data type violation detection failed: {e}")
    
    # Combine all results
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        return combined_results
    else:
        return pd.DataFrame() 