"""
Simple model training script for Smart Lead Scoring
"""

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingClassifier
import xgboost as xgb
import joblib
import json
import os
from pathlib import Path

def train_model():
    """Train a simple lead scoring model"""
    print("Loading data...")
    
    # Load the generated data. keep_default_na=False prevents pandas from
    # silently treating the literal region code "NA" (North America) as a missing value.
    df = pd.read_csv("data/generated_leads.csv", keep_default_na=False, na_values=[])
    print(f"Loaded {len(df)} leads")
    
    # Prepare features. This must match the LeadData fields the API accepts
    # (see api/enhanced_main.py) so requests map cleanly onto the trained columns.
    cat_cols = ['industry', 'company_size', 'region', 'source_channel', 'last_touch', 'job_title']
    num_cols = ['page_views_7d', 'emails_opened_30d', 'calls_last_30d', 'days_in_pipeline', 'deal_size_estimate']
    feature_cols = cat_cols + num_cols

    X = df[feature_cols]
    y = df['converted']

    print(f"Categorical features: {cat_cols}")
    print(f"Numerical features: {num_cols}")

    # Create preprocessing pipeline
    preprocessor = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
        ('num', StandardScaler(), num_cols)
    ])
    
    # Try XGBoost, fallback to GradientBoosting if it fails
    try:
        model = xgb.XGBClassifier(eval_metric='logloss', random_state=42, n_estimators=100)
        print("Using XGBoost classifier")
    except:
        model = GradientBoostingClassifier(random_state=42, n_estimators=100)
        print("Using GradientBoosting classifier")
    
    # Create full pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Training model...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate model
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"Model AUC Score: {auc_score:.4f}")
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    
    # Save model
    joblib.dump(pipeline, "models/model.joblib")
    
    # Save metadata
    metadata = {
        "feature_columns": feature_cols,
        "categorical_columns": cat_cols,
        "numerical_columns": num_cols,
        "model_type": type(model).__name__,
        "auc_score": float(auc_score),
        "trained_at": pd.Timestamp.now().isoformat()
    }
    
    with open("models/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Model saved successfully!")
    print(f"Features: {feature_cols}")
    print(f"AUC Score: {auc_score:.4f}")
    
    return pipeline, metadata

if __name__ == "__main__":
    train_model()
