import pandas as pd
from scipy import stats

def detect_numeric_anomalies(df: pd.DataFrame, z_thresh=3):
    results = []

    for col in df.select_dtypes(include=['number']).columns:
        # Get the series for this column and drop NA values
        series = df[col].dropna()
        
        # Skip if not enough data points
        if len(series) < 10:
            continue
            
        # Convert to numeric type to ensure we're working with numbers
        series = pd.to_numeric(series, errors='coerce').dropna()
        
        if len(series) < 10:  # Check again after conversion
            continue
            
        z_scores = stats.zscore(series)
        z_anomalies = series[(abs(z_scores) > z_thresh)]

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        iqr_anomalies = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]

        anomaly_indices = set(z_anomalies.index).union(iqr_anomalies.index)

        for idx in anomaly_indices:
            results.append({
                'column': col,
                'row_index': idx,
                'value': df.loc[idx, col],
                'issue_type': 'numeric_outlier'
            })
    
    return pd.DataFrame(results)



