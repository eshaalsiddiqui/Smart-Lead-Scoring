import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEADS_DATA_PATH = Path("data/generated_leads.csv")

# Global variables for model, metadata, and the scored leads cache
model = None
metadata = None
feature_columns = None
categorical_columns = None
numerical_columns = None
leads_cache = None  # pd.DataFrame of leads with model predictions attached


def load_leads_csv(path: Path) -> pd.DataFrame:
    """Load a leads CSV. keep_default_na=False stops pandas from silently
    treating the literal region code 'NA' (North America) as a missing value."""
    return pd.read_csv(path, keep_default_na=False, na_values=[])


def build_feature_frame(records: List[Dict]) -> pd.DataFrame:
    """Turn raw lead records into a frame matching the model's training schema.

    Missing/None categorical values become 'Unknown' (the bucket the model was
    trained with) and missing/None numerical values become 0 - never a blanket
    fillna(0) across both, which used to corrupt categorical columns into ints
    and crash the one-hot encoder.
    """
    df = pd.DataFrame(records)

    for col in categorical_columns:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = df[col].where(df[col].notna(), "Unknown")

    for col in numerical_columns:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df[feature_columns]


def score_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Attach conversion_probability, revenue_impact, next_best_action, and
    status to a dataframe of leads using the loaded model."""
    df = df.copy()
    features = build_feature_frame(df.to_dict("records"))
    df["conversion_probability"] = model.predict_proba(features)[:, 1]
    df["revenue_impact"] = df["conversion_probability"] * df["deal_size_estimate"]
    df["next_best_action"] = df["conversion_probability"].apply(get_next_best_action)
    df["status"] = df["next_best_action"].map(
        {"Call": "high", "Email": "medium", "Nurture": "low"}
    )
    return df


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model, metadata, and score the leads dataset on startup"""
    global model, metadata, feature_columns, categorical_columns, numerical_columns, leads_cache

    try:
        model_path = Path("models")
        if not model_path.exists():
            raise FileNotFoundError("Model directory not found")

        model = joblib.load(model_path / "model.joblib")

        with open(model_path / "metadata.json", "r") as f:
            metadata = json.load(f)

        feature_columns = metadata.get("feature_columns", [])
        categorical_columns = metadata.get("categorical_columns") or [
            c
            for c in feature_columns
            if c
            in [
                "industry",
                "company_size",
                "region",
                "source_channel",
                "last_touch",
                "job_title",
            ]
        ]
        numerical_columns = metadata.get("numerical_columns") or [
            c for c in feature_columns if c not in categorical_columns
        ]

        logger.info("Model loaded successfully")
        logger.info(f"Model type: {metadata.get('model_type', 'Unknown')}")
        logger.info(f"Features: {len(feature_columns)}")

        if LEADS_DATA_PATH.exists():
            leads_df = load_leads_csv(LEADS_DATA_PATH)
            leads_cache = score_leads(leads_df)
            logger.info(f"Scored {len(leads_cache)} leads from {LEADS_DATA_PATH}")
        else:
            leads_cache = pd.DataFrame()
            logger.warning(
                f"{LEADS_DATA_PATH} not found - /leads and /analytics endpoints will be empty"
            )

    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

    yield

    logger.info("Shutting down API")


app = FastAPI(
    title="Smart Lead Scoring API",
    description="ML-powered lead scoring and revenue impact prediction API",
    version="1.0.0",
    lifespan=lifespan,
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

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
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


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response: str


# Dependency to check if model is loaded
def get_model():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model


def get_metadata():
    if metadata is None:
        raise HTTPException(status_code=503, detail="Metadata not loaded")
    return metadata


def get_leads_cache():
    if leads_cache is None or leads_cache.empty:
        raise HTTPException(status_code=503, detail="Leads data not loaded")
    return leads_cache


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

    if (
        lead_data.calls_last_30d == 0
        and lead_data.days_in_pipeline
        and lead_data.days_in_pipeline > 30
    ):
        risk_factors.append("No recent calls and long pipeline time")

    if lead_data.deal_size_estimate < 1000:
        risk_factors.append("Small deal size")

    return risk_factors


def lead_row_to_dict(row: pd.Series) -> Dict:
    """Project a scored leads_cache row into the shape the frontend expects"""
    return {
        "lead_id": row.get("lead_id"),
        "company_name": row.get("company_name"),
        "contact_name": row.get("contact_name"),
        "email": row.get("email"),
        "industry": row.get("industry"),
        "company_size": row.get("company_size"),
        "region": row.get("region"),
        "conversion_probability": float(row["conversion_probability"]),
        "revenue_impact": float(row["revenue_impact"]),
        "next_best_action": row["next_best_action"],
        "status": row["status"],
    }


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_type=metadata.get("model_type") if metadata else None,
        features_count=len(feature_columns) if feature_columns else 0,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/predict/single", response_model=LeadPrediction)
async def predict_single_lead(lead: LeadData, model=Depends(get_model)):
    """Predict conversion probability for a single lead"""
    try:
        start_time = datetime.now()

        features_df = build_feature_frame([lead.dict()])
        conversion_prob = float(model.predict_proba(features_df)[0, 1])

        revenue_impact = calculate_revenue_impact(
            conversion_prob, lead.deal_size_estimate
        )
        next_action = get_next_best_action(conversion_prob)
        confidence = calculate_confidence_score(conversion_prob)
        risk_factors = identify_risk_factors(lead, conversion_prob)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"Prediction completed in {processing_time:.2f}ms for lead {lead.lead_id or 'unknown'}"
        )

        return LeadPrediction(
            lead_id=lead.lead_id,
            conversion_probability=conversion_prob,
            revenue_impact=revenue_impact,
            next_best_action=next_action,
            confidence_score=confidence,
            risk_factors=risk_factors,
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_leads(
    request: BatchPredictionRequest, model=Depends(get_model)
):
    """Predict conversion probabilities for multiple leads"""
    try:
        start_time = datetime.now()
        predictions = []

        for lead in request.leads:
            try:
                features_df = build_feature_frame([lead.dict()])
                conversion_prob = float(model.predict_proba(features_df)[0, 1])

                revenue_impact = calculate_revenue_impact(
                    conversion_prob, lead.deal_size_estimate
                )
                next_action = get_next_best_action(conversion_prob)
                confidence = calculate_confidence_score(conversion_prob)
                risk_factors = identify_risk_factors(lead, conversion_prob)

                predictions.append(
                    LeadPrediction(
                        lead_id=lead.lead_id,
                        conversion_probability=conversion_prob,
                        revenue_impact=revenue_impact,
                        next_best_action=next_action,
                        confidence_score=confidence,
                        risk_factors=risk_factors,
                    )
                )

            except Exception as e:
                logger.error(f"Error processing lead {lead.lead_id}: {str(e)}")
                predictions.append(
                    LeadPrediction(
                        lead_id=lead.lead_id,
                        conversion_probability=0.0,
                        revenue_impact=0.0,
                        next_best_action="Error",
                        confidence_score=0.0,
                        risk_factors=[f"Processing error: {str(e)}"],
                    )
                )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        conversion_probs = [p.conversion_probability for p in predictions]
        revenue_impacts = [p.revenue_impact for p in predictions]

        summary = {
            "total_leads": len(predictions),
            "avg_conversion_probability": float(np.mean(conversion_probs)),
            "total_revenue_impact": float(np.sum(revenue_impacts)),
            "high_priority_leads": sum(
                1 for p in predictions if p.conversion_probability >= 0.7
            ),
            "calls_needed": sum(1 for p in predictions if p.next_best_action == "Call"),
            "emails_needed": sum(
                1 for p in predictions if p.next_best_action == "Email"
            ),
            "nurture_needed": sum(
                1 for p in predictions if p.next_best_action == "Nurture"
            ),
        }

        logger.info(
            f"Batch prediction completed: {len(predictions)} leads in {processing_time:.2f}ms"
        )

        return BatchPredictionResponse(
            predictions=predictions, summary=summary, processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/predict/top-leads")
async def get_top_leads(
    limit: int = 10,
    min_probability: float = 0.0,
    min_revenue: float = 0.0,
    leads: pd.DataFrame = Depends(get_leads_cache),
):
    """Get top leads ranked by revenue impact, scored from data/generated_leads.csv"""
    filtered = (
        leads[
            (leads["conversion_probability"] >= min_probability)
            & (leads["revenue_impact"] >= min_revenue)
        ]
        .sort_values("revenue_impact", ascending=False)
        .head(limit)
    )

    return {"leads": [lead_row_to_dict(row) for _, row in filtered.iterrows()]}


@app.get("/leads")
async def list_leads(
    search: str = "",
    status: str = "all",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    leads: pd.DataFrame = Depends(get_leads_cache),
):
    """List scored leads with search/status filtering and pagination, backing the Leads page"""
    filtered = leads
    if search:
        needle = search.lower()
        mask = filtered["company_name"].str.lower().str.contains(
            needle, na=False
        ) | filtered["contact_name"].str.lower().str.contains(needle, na=False)
        filtered = filtered[mask]
    if status != "all":
        filtered = filtered[filtered["status"] == status]

    filtered = filtered.sort_values("revenue_impact", ascending=False)
    total = len(filtered)
    start = (page - 1) * limit
    page_rows = filtered.iloc[start : start + limit]

    return {
        "leads": [lead_row_to_dict(row) for _, row in page_rows.iterrows()],
        "total": total,
        "page": page,
        "limit": limit,
    }


@app.get("/analytics/summary")
async def get_analytics_summary(leads: pd.DataFrame = Depends(get_leads_cache)):
    """Aggregate real metrics from the scored leads cache for the dashboard/analytics pages"""
    total_leads = len(leads)
    conversion_rate = (
        float(leads["converted"].mean())
        if "converted" in leads.columns
        else float(leads["conversion_probability"].mean())
    )
    total_revenue = float(leads["revenue_impact"].sum())
    high_priority_leads = int((leads["status"] == "high").sum())

    industry_breakdown = (
        leads.groupby("industry")
        .agg(leads=("lead_id", "count"), conversions=("converted", "sum"))
        .reset_index()
        .sort_values("leads", ascending=False)
        .to_dict("records")
    )

    monthly = leads.copy()
    monthly["month_period"] = pd.to_datetime(monthly["created_date"]).dt.to_period("M")
    monthly_trend = (
        monthly.groupby("month_period")
        .agg(leads=("lead_id", "count"), conversions=("converted", "sum"))
        .reset_index()
        .sort_values("month_period")
    )
    monthly_trend["month"] = monthly_trend["month_period"].dt.strftime("%b %Y")
    monthly_trend = (
        monthly_trend[["month", "leads", "conversions"]].tail(12).to_dict("records")
    )

    action_counts = leads["next_best_action"].value_counts()
    priority_counts = leads["status"].value_counts()

    return {
        "totalLeads": total_leads,
        "conversionRate": conversion_rate,
        "totalRevenue": total_revenue,
        "highPriorityLeads": high_priority_leads,
        "industryBreakdown": industry_breakdown,
        "monthlyTrend": monthly_trend,
        "actionStats": {
            "callsNeeded": int(action_counts.get("Call", 0)),
            "emailsNeeded": int(action_counts.get("Email", 0)),
            "nurtureNeeded": int(action_counts.get("Nurture", 0)),
        },
        "priorityDistribution": {
            "high": int(priority_counts.get("high", 0)),
            "medium": int(priority_counts.get("medium", 0)),
            "low": int(priority_counts.get("low", 0)),
        },
    }


@app.post("/chatbot/query", response_model=ChatResponse)
async def chatbot_query(
    request: ChatRequest, leads: pd.DataFrame = Depends(get_leads_cache)
):
    """Answer lead/CRM questions using the real scored leads cache (rule-based, not an LLM)"""
    message = request.message.lower()

    if "top" in message and "lead" in message or "best lead" in message:
        top = leads.sort_values("revenue_impact", ascending=False).head(5)
        lines = [
            f"{i+1}. **{row['company_name']}** - {row['conversion_probability']*100:.0f}% conversion probability, "
            f"${row['revenue_impact']:,.0f} revenue impact"
            for i, (_, row) in enumerate(top.iterrows())
        ]
        return ChatResponse(
            response="Here are your top 5 leads by revenue impact:\n\n"
            + "\n".join(lines)
        )

    if "conversion" in message or "performance" in message:
        rate = leads["converted"].mean() * 100
        total_revenue = leads["revenue_impact"].sum()
        high_priority = (leads["status"] == "high").sum()
        avg_deal = leads["deal_size_estimate"].mean()
        return ChatResponse(
            response=(
                f"Current performance:\n\n"
                f"- Conversion rate: {rate:.1f}%\n"
                f"- Total pipeline value: ${total_revenue:,.0f}\n"
                f"- High priority leads: {high_priority}\n"
                f"- Average deal size: ${avg_deal:,.0f}"
            )
        )

    if "industry" in message or "sector" in message:
        breakdown = (
            leads.groupby("industry")
            .agg(leads=("lead_id", "count"), conv_rate=("converted", "mean"))
            .sort_values("leads", ascending=False)
            .head(5)
        )
        lines = [
            f"{i+1}. {industry} - {row['leads']} leads, {row['conv_rate']*100:.0f}% conversion rate"
            for i, (industry, row) in enumerate(breakdown.iterrows())
        ]
        return ChatResponse(
            response="Industry breakdown (by lead volume):\n\n" + "\n".join(lines)
        )

    if "action" in message or "next step" in message or "attention" in message:
        action_counts = leads["next_best_action"].value_counts()
        urgent = (
            leads[leads["next_best_action"] == "Call"]
            .sort_values("revenue_impact", ascending=False)
            .head(3)
        )
        urgent_names = (
            ", ".join(urgent["company_name"].tolist()) if not urgent.empty else "none"
        )
        return ChatResponse(
            response=(
                f"Recommended actions:\n\n"
                f"- Calls needed: {int(action_counts.get('Call', 0))}\n"
                f"- Emails needed: {int(action_counts.get('Email', 0))}\n"
                f"- Nurture campaign: {int(action_counts.get('Nurture', 0))}\n\n"
                f"Top call priorities: {urgent_names}"
            )
        )

    if "revenue" in message or "pipeline" in message or "forecast" in message:
        high = leads[leads["status"] == "high"]["revenue_impact"].sum()
        medium = leads[leads["status"] == "medium"]["revenue_impact"].sum()
        low = leads[leads["status"] == "low"]["revenue_impact"].sum()
        top = leads.sort_values("revenue_impact", ascending=False).head(3)
        top_lines = [
            f"{i+1}. {row['company_name']} - ${row['revenue_impact']:,.0f} ({row['conversion_probability']*100:.0f}% probability)"
            for i, (_, row) in enumerate(top.iterrows())
        ]
        return ChatResponse(
            response=(
                f"Pipeline value: ${leads['revenue_impact'].sum():,.0f}\n\n"
                f"- High probability deals: ${high:,.0f}\n"
                f"- Medium probability deals: ${medium:,.0f}\n"
                f"- Low probability deals: ${low:,.0f}\n\n"
                f"Top opportunities:\n" + "\n".join(top_lines)
            )
        )

    if "help" in message or "what can you do" in message:
        return ChatResponse(
            response=(
                "I can help you with:\n\n"
                '- "Who are my top leads?"\n'
                '- "What\'s our conversion rate?"\n'
                '- "What\'s our industry breakdown?"\n'
                '- "Which leads need immediate attention?"\n'
                '- "What\'s our revenue forecast?"'
            )
        )

    return ChatResponse(
        response=(
            f"I can analyze your {len(leads)} scored leads. Try asking about top leads, "
            f"conversion rate, industry breakdown, next actions, or revenue forecast."
        )
    )


@app.get("/model/info")
async def get_model_info(metadata=Depends(get_metadata)):
    """Get information about the loaded model"""
    return {
        "model_type": metadata.get("model_type"),
        "trained_at": metadata.get("trained_at"),
        "auc_score": metadata.get("auc_score"),
        "feature_count": len(feature_columns),
        "features": (
            feature_columns[:10] if len(feature_columns) > 10 else feature_columns
        ),
        "preprocessor_type": metadata.get("preprocessor_type"),
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
