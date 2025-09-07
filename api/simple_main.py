from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import joblib
import json
import pandas as pd
import numpy as np
from pathlib import Path

app = FastAPI(title="Smart Lead Scoring API")

# Load model and metadata
try:
    model = joblib.load("models/model.joblib")
    with open("models/metadata.json", 'r') as f:
        metadata = json.load(f)
    feature_columns = metadata.get('feature_columns', [])
    print(f"Model loaded: {metadata.get('model_type')}")
    print(f"Features: {feature_columns}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    metadata = {}
    feature_columns = []

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeadData(BaseModel):
    company_name: str
    email: str
    industry: str
    company_size: str
    region: str
    deal_size_estimate: float
    page_views_7d: int = 0
    emails_opened_30d: int = 0
    calls_last_30d: int = 0

class PredictionResponse(BaseModel):
    conversion_probability: float
    revenue_impact: float
    next_best_action: str

@app.get("/health")
def health():
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "model_type": metadata.get('model_type', 'Unknown'),
        "features_count": len(feature_columns)
    }

@app.post("/predict/single", response_model=PredictionResponse)
def predict_single_lead(lead: LeadData):
    """Predict conversion probability for a single lead"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Prepare features in the same order as training
        data = {
            'industry': lead.industry,
            'company_size': lead.company_size,
            'region': lead.region,
            'last_touch': 'demo_request',  # Default value
            'page_views_7d': lead.page_views_7d,
            'emails_opened_30d': lead.emails_opened_30d,
            'calls_last_30d': lead.calls_last_30d,
            'deal_size_estimate': lead.deal_size_estimate
        }
        
        # Create DataFrame
        df = pd.DataFrame([data])
        
        # Make prediction
        conversion_prob = float(model.predict_proba(df)[0, 1])
        
        # Calculate revenue impact
        revenue_impact = conversion_prob * lead.deal_size_estimate
        
        # Determine next best action with more realistic thresholds
        if conversion_prob >= 0.8:
            next_action = "Call"
        elif conversion_prob >= 0.5:
            next_action = "Email"
        else:
            next_action = "Nurture"
        
        return PredictionResponse(
            conversion_probability=conversion_prob,
            revenue_impact=revenue_impact,
            next_best_action=next_action
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/batch")
def predict_batch_leads(leads: List[LeadData]):
    """Predict conversion probabilities for multiple leads"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    predictions = []
    
    for lead in leads:
        try:
            # Prepare features
            data = {
                'industry': lead.industry,
                'company_size': lead.company_size,
                'region': lead.region,
                'last_touch': 'demo_request',
                'page_views_7d': lead.page_views_7d,
                'emails_opened_30d': lead.emails_opened_30d,
                'calls_last_30d': lead.calls_last_30d,
                'deal_size_estimate': lead.deal_size_estimate
            }
            
            df = pd.DataFrame([data])
            conversion_prob = float(model.predict_proba(df)[0, 1])
            revenue_impact = conversion_prob * lead.deal_size_estimate
            
            if conversion_prob >= 0.8:
                next_action = "Call"
            elif conversion_prob >= 0.5:
                next_action = "Email"
            else:
                next_action = "Nurture"
            
            predictions.append({
                "company_name": lead.company_name,
                "conversion_probability": conversion_prob,
                "revenue_impact": revenue_impact,
                "next_best_action": next_action
            })
            
        except Exception as e:
            predictions.append({
                "company_name": lead.company_name,
                "conversion_probability": 0.0,
                "revenue_impact": 0.0,
                "next_best_action": "Error",
                "error": str(e)
            })
    
    return {
        "predictions": predictions,
        "total_leads": len(predictions),
        "avg_conversion_probability": np.mean([p["conversion_probability"] for p in predictions]),
        "total_revenue_impact": sum([p["revenue_impact"] for p in predictions])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
