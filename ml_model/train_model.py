"""
Enhanced ML Model Training for Smart Lead Scoring CRM
Includes experiment tracking with MLflow and revenue impact scoring
"""

import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, List

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (
    roc_auc_score, precision_recall_fscore_support, classification_report,
    confusion_matrix, roc_curve, precision_recall_curve
)
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import lightgbm as lgb

import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.lightgbm
from mlflow.tracking import MlflowClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeadScoringModel:
    def __init__(self, experiment_name: str = "lead_scoring"):
        self.experiment_name = experiment_name
        self.model = None
        self.preprocessor = None
        self.feature_columns = None
        self.label_encoders = {}
        
        # Set up MLflow
        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()
    
    def load_data(self, data_path: str) -> pd.DataFrame:
        """Load and prepare training data"""
        logger.info(f"Loading data from {data_path}")
        
        if data_path.endswith('.parquet'):
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} features")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training"""
        logger.info("Preparing features for training")
        
        # Define feature columns
        categorical_features = [
            'industry', 'company_size', 'region', 'source_channel', 
            'last_touch', 'job_title', 'company_size_category', 'lead_quality'
        ]
        
        numerical_features = [
            'page_views_7d', 'emails_opened_30d', 'calls_last_30d',
            'days_in_pipeline', 'deal_size_estimate', 'engagement_score',
            'days_since_created', 'days_since_last_activity'
        ]
        
        # Create additional features
        df = self._create_engineered_features(df)
        
        # Select features that exist in the dataframe
        available_cat = [col for col in categorical_features if col in df.columns]
        available_num = [col for col in numerical_features if col in df.columns]
        
        self.feature_columns = available_cat + available_num
        
        # Prepare target
        if 'converted' in df.columns:
            y = df['converted']
        else:
            # If no conversion data, create synthetic target based on probability
            y = (df['conversion_probability'] > 0.5).astype(int)
        
        # Prepare features
        X = df[self.feature_columns].copy()
        
        # Handle missing values
        X[available_cat] = X[available_cat].fillna('Unknown')
        X[available_num] = X[available_num].fillna(0)
        
        logger.info(f"Prepared {len(X)} samples with {len(self.feature_columns)} features")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")
        
        return X, y
    
    def _create_engineered_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create additional engineered features"""
        df = df.copy()
        
        # Engagement velocity (rate of change)
        if 'page_views_7d' in df.columns and 'days_since_created' in df.columns:
            df['page_velocity'] = df['page_views_7d'] / (df['days_since_created'] + 1)
        
        # Email engagement rate
        if 'emails_opened_30d' in df.columns:
            df['email_engagement_rate'] = df['emails_opened_30d'] / 30
        
        # Call frequency
        if 'calls_last_30d' in df.columns and 'days_since_created' in df.columns:
            df['call_frequency'] = df['calls_last_30d'] / (df['days_since_created'] + 1)
        
        # Deal size category
        if 'deal_size_estimate' in df.columns:
            df['deal_size_category'] = pd.cut(
                df['deal_size_estimate'],
                bins=[0, 1000, 5000, 15000, 50000, float('inf')],
                labels=['Small', 'Medium', 'Large', 'Enterprise', 'Enterprise+']
            )
        
        # Lead age category
        if 'days_since_created' in df.columns:
            df['lead_age_category'] = pd.cut(
                df['days_since_created'],
                bins=[0, 7, 30, 90, 180, float('inf')],
                labels=['New', 'Recent', 'Mature', 'Old', 'Stale']
            )
        
        return df
    
    def create_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        """Create preprocessing pipeline"""
        categorical_features = X.select_dtypes(include=['object']).columns.tolist()
        numerical_features = X.select_dtypes(include=[np.number]).columns.tolist()
        
        preprocessor = ColumnTransformer([
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('num', StandardScaler(), numerical_features)
        ])
        
        return preprocessor
    
    def train_models(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict:
        """Train multiple models and select the best one"""
        logger.info("Training multiple models")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Create preprocessor
        self.preprocessor = self.create_preprocessor(X_train)
        
        # Define models to test
        models = {
            'xgboost': xgb.XGBClassifier(
                eval_metric='logloss',
                random_state=42,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1
            ),
            'lightgbm': lgb.LGBMClassifier(
                random_state=42,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                verbose=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                random_state=42,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1
            ),
            'random_forest': RandomForestClassifier(
                random_state=42,
                n_estimators=100,
                max_depth=10
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        best_model = None
        best_score = 0
        best_model_name = None
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}")
            
            with mlflow.start_run(run_name=f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                # Create pipeline
                pipeline = Pipeline([
                    ('preprocessor', self.preprocessor),
                    ('classifier', model)
                ])
                
                # Train model
                pipeline.fit(X_train, y_train)
                
                # Evaluate model
                y_pred = pipeline.predict(X_test)
                y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
                
                # Calculate metrics
                auc_score = roc_auc_score(y_test, y_pred_proba)
                precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
                
                # Cross-validation score
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='roc_auc')
                
                # Log metrics to MLflow
                mlflow.log_metric("auc_score", auc_score)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("recall", recall)
                mlflow.log_metric("f1_score", f1)
                mlflow.log_metric("cv_auc_mean", cv_scores.mean())
                mlflow.log_metric("cv_auc_std", cv_scores.std())
                
                # Log parameters
                if hasattr(model, 'get_params'):
                    mlflow.log_params(model.get_params())
                
                # Log model
                if name == 'xgboost':
                    mlflow.xgboost.log_model(model, "model")
                elif name == 'lightgbm':
                    mlflow.lightgbm.log_model(model, "model")
                else:
                    mlflow.sklearn.log_model(pipeline, "model")
                
                results[name] = {
                    'auc_score': auc_score,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'cv_scores': cv_scores,
                    'model': pipeline
                }
                
                # Track best model
                if auc_score > best_score:
                    best_score = auc_score
                    best_model = pipeline
                    best_model_name = name
                
                logger.info(f"{name} - AUC: {auc_score:.4f}, F1: {f1:.4f}")
        
        self.model = best_model
        logger.info(f"Best model: {best_model_name} with AUC: {best_score:.4f}")
        
        return results
    
    def calculate_revenue_impact(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Calculate revenue impact scores for leads"""
        logger.info("Calculating revenue impact scores")
        
        # Get conversion probabilities
        conversion_probs = self.model.predict_proba(X)[:, 1]
        
        # Get deal size estimates
        if 'deal_size_estimate' in X.columns:
            deal_sizes = X['deal_size_estimate']
        else:
            # Use average deal size if not available
            deal_sizes = pd.Series([5000] * len(X), index=X.index)
        
        # Calculate revenue impact
        revenue_impact = conversion_probs * deal_sizes
        
        # Create results dataframe
        results_df = pd.DataFrame({
            'conversion_probability': conversion_probs,
            'deal_size_estimate': deal_sizes,
            'revenue_impact': revenue_impact,
            'converted': y
        })
        
        # Add ranking
        results_df['revenue_rank'] = results_df['revenue_impact'].rank(ascending=False)
        
        # Add next best action
        results_df['next_best_action'] = results_df['conversion_probability'].apply(
            lambda x: 'Call' if x >= 0.7 else 'Email' if x >= 0.4 else 'Nurture'
        )
        
        logger.info(f"Revenue impact calculated for {len(results_df)} leads")
        logger.info(f"Total pipeline value: ${results_df['revenue_impact'].sum():,.0f}")
        
        return results_df
    
    def save_model(self, model_path: str = "models"):
        """Save trained model and metadata"""
        logger.info(f"Saving model to {model_path}")
        
        model_dir = Path(model_path)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        joblib.dump(self.model, model_dir / "model.joblib")
        
        # Save metadata
        metadata = {
            'feature_columns': self.feature_columns,
            'model_type': type(self.model.named_steps['classifier']).__name__,
            'trained_at': datetime.now().isoformat(),
            'preprocessor_type': type(self.preprocessor).__name__
        }
        
        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Model saved successfully")
    
    def load_model(self, model_path: str = "models"):
        """Load trained model and metadata"""
        logger.info(f"Loading model from {model_path}")
        
        model_dir = Path(model_path)
        
        # Load model
        self.model = joblib.load(model_dir / "model.joblib")
        
        # Load metadata
        with open(model_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        self.feature_columns = metadata['feature_columns']
        
        logger.info("Model loaded successfully")
        return metadata

def main():
    """Main training function"""
    logger.info("Starting model training pipeline")
    
    # Initialize model trainer
    trainer = LeadScoringModel("lead_scoring_production")
    
    # Load data
    data_path = "data/processed/master_leads.parquet"
    if not Path(data_path).exists():
        # Fallback to CSV if parquet doesn't exist
        data_path = "data/generated_leads.csv"
    
    df = trainer.load_data(data_path)
    
    # Prepare features
    X, y = trainer.prepare_features(df)
    
    # Train models
    results = trainer.train_models(X, y)
    
    # Calculate revenue impact
    revenue_impact = trainer.calculate_revenue_impact(X, y)
    
    # Save model
    trainer.save_model()
    
    # Save revenue impact results
    revenue_impact.to_csv("data/revenue_impact_analysis.csv", index=False)
    
    logger.info("Model training completed successfully")
    
    # Print summary
    print("\n" + "="*50)
    print("TRAINING SUMMARY")
    print("="*50)
    for name, result in results.items():
        print(f"{name.upper()}:")
        print(f"  AUC Score: {result['auc_score']:.4f}")
        print(f"  F1 Score: {result['f1_score']:.4f}")
        print(f"  CV AUC: {result['cv_scores'].mean():.4f} ± {result['cv_scores'].std():.4f}")
        print()
    
    print(f"Total Pipeline Value: ${revenue_impact['revenue_impact'].sum():,.0f}")
    print(f"Average Revenue Impact: ${revenue_impact['revenue_impact'].mean():,.0f}")

if __name__ == "__main__":
    main()
