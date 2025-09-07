from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import joblib
import json
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union
from datetime import datetime
import logging
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model and metadata
model = None
metadata = None
feature_columns = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup"""
    global model, metadata, feature_columns
    
    try:
        # Load model and metadata
        model_path = Path("models")
        if not model_path.exists():
            raise FileNotFoundError("Model directory not found")
        
        model = joblib.load(model_path / "model.joblib")
        
        with open(model_path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        feature_columns = metadata.get('feature_columns', [])
        
        logger.info("Model loaded successfully")
        logger.info(f"Model type: {metadata.get('model_type', 'Unknown')}")
        logger.info(f"Features: {len(feature_columns)}")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down API")

app = FastAPI(
    title="Smart Lead Scoring API",
    description="ML-powered lead scoring and revenue impact prediction API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LeadData(BaseModel):
    lead_id: Optional[str] = None
    company_name: str = Field(..., description="Company name")
    contact_name: Optional[str] = None
    email: str = Field(..., description="Contact email")
    job_title: Optional[str] = None
    industry: str = Field(..., description="Industry sector")
    company_size: str = Field(..., description="Company size category")
    region: str = Field(..., description="Geographic region")
    source_channel: Optional[str] = None
    decision_maker: Optional[bool] = None
    last_touch: Optional[str] = None
    page_views_7d: int = Field(0, ge=0, description="Page views in last 7 days")
    emails_opened_30d: int = Field(0, ge=0, description="Emails opened in last 30 days")
    calls_last_30d: int = Field(0, ge=0, description="Calls in last 30 days")
    days_in_pipeline: Optional[int] = None
    deal_size_estimate: float = Field(..., gt=0, description="Estimated deal size")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

class LeadPrediction(BaseModel):
    lead_id: Optional[str]
    conversion_probability: float = Field(..., ge=0, le=1)
    revenue_impact: float = Field(..., ge=0)
    next_best_action: str
    confidence_score: float = Field(..., ge=0, le=1)
    risk_factors: List[str] = []

class BatchPredictionRequest(BaseModel):
    leads: List[LeadData] = Field(..., min_items=1, max_items=1000)

class BatchPredictionResponse(BaseModel):
    predictions: List[LeadPrediction]
    summary: Dict[str, Union[int, float]]
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_type: Optional[str] = None
    features_count: int
    timestamp: str

# Dependency to check if model is loaded
def get_model():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model

def get_metadata():
    if metadata is None:
        raise HTTPException(status_code=503, detail="Metadata not loaded")
    return metadata

# Utility functions
def calculate_revenue_impact(conversion_prob: float, deal_size: float) -> float:
    """Calculate revenue impact score"""
    return conversion_prob * deal_size

def get_next_best_action(conversion_prob: float) -> str:
    """Determine next best action based on conversion probability"""
    if conversion_prob >= 0.7:
        return "Call"
    elif conversion_prob >= 0.4:
        return "Email"
    else:
        return "Nurture"

def calculate_confidence_score(conversion_prob: float) -> float:
    """Calculate confidence score based on probability distribution"""
    # Higher confidence for probabilities closer to 0 or 1
    return 1 - 2 * abs(conversion_prob - 0.5)

def identify_risk_factors(lead_data: LeadData, conversion_prob: float) -> List[str]:
    """Identify potential risk factors for the lead"""
    risk_factors = []
    
    if conversion_prob < 0.3:
        risk_factors.append("Low conversion probability")
    
    if lead_data.page_views_7d == 0:
        risk_factors.append("No recent website activity")
    
    if lead_data.emails_opened_30d == 0:
        risk_factors.append("No email engagement")
    
    if lead_data.calls_last_30d == 0 and lead_data.days_in_pipeline and lead_data.days_in_pipeline > 30:
        risk_factors.append("No recent calls and long pipeline time")
    
    if lead_data.deal_size_estimate < 1000:
        risk_factors.append("Small deal size")
    
    return risk_factors

def prepare_features(lead_data: LeadData) -> pd.DataFrame:
    """Prepare features for model prediction"""
    # Convert to dictionary
    data = lead_data.dict()
    
    # Create DataFrame
    df = pd.DataFrame([data])
    
    # Add missing columns with default values
    for col in feature_columns:
        if col not in df.columns:
            if col in ['engagement_score', 'days_since_created', 'days_since_last_activity']:
                df[col] = 0
            elif col in ['company_size_category', 'lead_quality', 'deal_size_category', 'lead_age_category']:
                df[col] = 'Unknown'
            else:
                df[col] = None
    
    # Reorder columns to match training data
    df = df[feature_columns]
    
    # Fill missing values
    df = df.fillna(0)
    
    return df

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_type=metadata.get('model_type') if metadata else None,
        features_count=len(feature_columns) if feature_columns else 0,
        timestamp=datetime.now().isoformat()
    )

@app.post("/predict/single", response_model=LeadPrediction)
async def predict_single_lead(lead: LeadData, model=Depends(get_model)):
    """Predict conversion probability for a single lead"""
    try:
        start_time = datetime.now()
        
        # Prepare features
        features_df = prepare_features(lead)
        
        # Make prediction
        conversion_prob = float(model.predict_proba(features_df)[0, 1])
        
        # Calculate additional metrics
        revenue_impact = calculate_revenue_impact(conversion_prob, lead.deal_size_estimate)
        next_action = get_next_best_action(conversion_prob)
        confidence = calculate_confidence_score(conversion_prob)
        risk_factors = identify_risk_factors(lead, conversion_prob)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"Prediction completed in {processing_time:.2f}ms for lead {lead.lead_id or 'unknown'}")
        
        return LeadPrediction(
            lead_id=lead.lead_id,
            conversion_probability=conversion_prob,
            revenue_impact=revenue_impact,
            next_best_action=next_action,
            confidence_score=confidence,
            risk_factors=risk_factors
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_leads(
    request: BatchPredictionRequest, 
    model=Depends(get_model),
    background_tasks: BackgroundTasks = None
):
    """Predict conversion probabilities for multiple leads"""
    try:
        start_time = datetime.now()
        predictions = []
        
        for lead in request.leads:
            try:
                # Prepare features
                features_df = prepare_features(lead)
                
                # Make prediction
                conversion_prob = float(model.predict_proba(features_df)[0, 1])
                
                # Calculate additional metrics
                revenue_impact = calculate_revenue_impact(conversion_prob, lead.deal_size_estimate)
                next_action = get_next_best_action(conversion_prob)
                confidence = calculate_confidence_score(conversion_prob)
                risk_factors = identify_risk_factors(lead, conversion_prob)
                
                predictions.append(LeadPrediction(
                    lead_id=lead.lead_id,
                    conversion_probability=conversion_prob,
                    revenue_impact=revenue_impact,
                    next_best_action=next_action,
                    confidence_score=confidence,
                    risk_factors=risk_factors
                ))
                
            except Exception as e:
                logger.error(f"Error processing lead {lead.lead_id}: {str(e)}")
                # Add error prediction
                predictions.append(LeadPrediction(
                    lead_id=lead.lead_id,
                    conversion_probability=0.0,
                    revenue_impact=0.0,
                    next_best_action="Error",
                    confidence_score=0.0,
                    risk_factors=[f"Processing error: {str(e)}"]
                ))
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calculate summary statistics
        conversion_probs = [p.conversion_probability for p in predictions]
        revenue_impacts = [p.revenue_impact for p in predictions]
        
        summary = {
            "total_leads": len(predictions),
            "avg_conversion_probability": float(np.mean(conversion_probs)),
            "total_revenue_impact": float(np.sum(revenue_impacts)),
            "high_priority_leads": sum(1 for p in predictions if p.conversion_probability >= 0.7),
            "calls_needed": sum(1 for p in predictions if p.next_best_action == "Call"),
            "emails_needed": sum(1 for p in predictions if p.next_best_action == "Email"),
            "nurture_needed": sum(1 for p in predictions if p.next_best_action == "Nurture")
        }
        
        logger.info(f"Batch prediction completed: {len(predictions)} leads in {processing_time:.2f}ms")
        
        return BatchPredictionResponse(
            predictions=predictions,
            summary=summary,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/predict/top-leads")
async def get_top_leads(
    limit: int = 10,
    min_probability: float = 0.0,
    min_revenue: float = 0.0,
    model=Depends(get_model)
):
    """Get top leads based on revenue impact (requires data source)"""
    # This would typically query a database
    # For now, return a placeholder response
    return {
        "message": "Top leads endpoint - requires database integration",
        "parameters": {
            "limit": limit,
            "min_probability": min_probability,
            "min_revenue": min_revenue
        }
    }

@app.get("/model/info")
async def get_model_info(metadata=Depends(get_metadata)):
    """Get information about the loaded model"""
    return {
        "model_type": metadata.get('model_type'),
        "trained_at": metadata.get('trained_at'),
        "feature_count": len(feature_columns),
        "features": feature_columns[:10] if len(feature_columns) > 10 else feature_columns,
        "preprocessor_type": metadata.get('preprocessor_type')
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
