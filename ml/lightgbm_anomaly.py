import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Set a fixed random seed for reproducibility
np.random.seed(42)

def prepare_data_for_lightgbm(df: pd.DataFrame):
    """Prepare data for LightGBM without removing anomalies"""
    df_processed = df.copy()
    
    # Handle missing values without removing patterns
    for col in df_processed.columns:
        if df_processed[col].dtype in ['object', 'category']:
            # For categorical, fill with 'MISSING' to preserve missing pattern
            df_processed[col] = df_processed[col].fillna('MISSING')
        else:
            # For numeric, fill with -999 to preserve missing pattern
            df_processed[col] = df_processed[col].fillna(-999)
    
    # Basic label encoding for categorical columns
    label_encoders = {}
    for col in df_processed.select_dtypes(include=['object', 'category']).columns:
        le = LabelEncoder()
        df_processed[col] = le.fit_transform(df_processed[col].astype(str))
        label_encoders[col] = le
    
    return df_processed, label_encoders

def train_lightgbm_anomaly_detector(df: pd.DataFrame, contamination=0.1):
    """Train LightGBM for anomaly detection"""
    # Prepare data
    df_processed, label_encoders = prepare_data_for_lightgbm(df)
    
    # Create synthetic labels (assuming most data is normal)
    n_samples = len(df_processed)
    n_anomalies = int(contamination * n_samples)
    
    # Set the random seed immediately before random operations for reproducibility
    np.random.seed(42)
    # Create labels: 0 for normal, 1 for anomaly
    labels = np.zeros(n_samples)
    # Randomly mark some samples as anomalies for training
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    labels[anomaly_indices] = 1
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df_processed, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # LightGBM parameters for anomaly detection
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'is_unbalance': True,  # Important for anomaly detection
        'seed': 42,  # Ensures reproducibility
        'num_threads': 1  # Ensures strict reproducibility
    }
    
    # Train model
    train_data = lgb.Dataset(X_train, label=y_train)
    model = lgb.train(params, train_data, num_boost_round=100)
    
    return model, label_encoders

def detect_lightgbm_anomalies(df: pd.DataFrame, model, label_encoders, threshold=0.5):
    """Detect anomalies using trained LightGBM model"""
    # Prepare data using same encoders
    df_processed, _ = prepare_data_for_lightgbm(df)
    
    # Get predictions
    predictions = model.predict(df_processed)
    
    # Find anomalies based on threshold
    anomaly_indices = np.where(predictions > threshold)[0]
    
    results = []
    for idx in anomaly_indices:
        results.append({
            'row_index': idx,
            'anomaly_score': predictions[idx],
            'issue_type': 'complex_pattern_anomaly'
        })
    
    return pd.DataFrame(results), predictions

def get_feature_importance(model, df: pd.DataFrame):
    """Get feature importance from LightGBM model"""
    importance = model.feature_importance(importance_type='gain')
    feature_names = df.columns.tolist()
    
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    return feature_importance 