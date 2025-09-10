import pandas as pd
def detect_categorical_anomalies(df: pd.DataFrame, min_frq=0.01):
    results = []

    for col in df.select_dtypes(include=['object', 'category']).columns:
        series = df[col].dropna()
        value_counts = series.value_counts(normalize=True)
        rare_values = value_counts[value_counts < min_frq].index.to_list()

        for idx, val in series.items():
            if val in rare_values:
                results.append({
                    'column': col,
                    'row_index': idx,
                    'value': val,
                    'issue_type': 'rare_category'
                })
    return pd.DataFrame(results)