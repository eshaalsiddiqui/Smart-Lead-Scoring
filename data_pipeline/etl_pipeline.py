"""
ETL Pipeline for Smart Lead Scoring CRM
Processes daily lead data using Prefect for orchestration
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from lead_data_simulator import LeadDataSimulator
from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret
from prefect.filesystems import LocalFileSystem
from prefect.task_runners import SequentialTaskRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@task
def extract_daily_leads(date: datetime, num_leads: int = 50) -> pd.DataFrame:
    """Extract daily lead data from simulator"""
    logger = get_run_logger()
    logger.info(f"Extracting leads for date: {date.strftime('%Y-%m-%d')}")

    simulator = LeadDataSimulator()
    leads_df = simulator.generate_daily_batch(date, num_leads)

    logger.info(f"Extracted {len(leads_df)} leads")
    return leads_df


@task
def transform_leads(raw_leads: pd.DataFrame) -> pd.DataFrame:
    """Transform and clean lead data"""
    logger = get_run_logger()
    logger.info("Transforming lead data")

    df = raw_leads.copy()

    # Data cleaning and validation
    df = df.dropna(subset=["email", "company_name"])

    # Standardize company sizes
    size_mapping = {
        "1-10": "Small",
        "11-50": "Small-Medium",
        "51-200": "Medium",
        "201-1000": "Large",
        "1001-5000": "Enterprise",
        "5000+": "Enterprise+",
    }
    df["company_size_category"] = df["company_size"].map(size_mapping)

    # Create engagement score
    df["engagement_score"] = (
        df["page_views_7d"] * 0.3
        + df["emails_opened_30d"] * 0.4
        + df["calls_last_30d"] * 0.3
    )

    # Create lead quality score
    df["lead_quality"] = np.where(
        df["decision_maker"] == True,
        "High",
        np.where(
            df["engagement_score"] > df["engagement_score"].quantile(0.7),
            "Medium",
            "Low",
        ),
    )

    # Add data quality flags
    df["data_quality_score"] = np.where(
        (df["email"].str.contains("@", na=False))
        & (df["deal_size_estimate"] > 0)
        & (df["page_views_7d"] >= 0),
        1.0,
        0.0,
    )

    # Create time-based features
    df["created_date"] = pd.to_datetime(df["created_date"])
    df["last_activity"] = pd.to_datetime(df["last_activity"])
    df["days_since_created"] = (datetime.now() - df["created_date"]).dt.days
    df["days_since_last_activity"] = (datetime.now() - df["last_activity"]).dt.days

    logger.info(
        f"Transformed {len(df)} leads with {df['data_quality_score'].sum()} high-quality records"
    )
    return df


@task
def load_leads_to_warehouse(transformed_leads: pd.DataFrame, date: datetime) -> str:
    """Load transformed leads to data warehouse"""
    logger = get_run_logger()
    logger.info("Loading leads to data warehouse")

    # Create data directory if it doesn't exist
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save to parquet for better performance
    filepath = data_dir / f"leads_{date.strftime('%Y%m%d')}.parquet"
    transformed_leads.to_parquet(filepath, index=False)

    # Also append to master leads file
    master_file = data_dir / "master_leads.parquet"
    if master_file.exists():
        existing_df = pd.read_parquet(master_file)
        combined_df = pd.concat([existing_df, transformed_leads], ignore_index=True)
    else:
        combined_df = transformed_leads

    combined_df.to_parquet(master_file, index=False)

    logger.info(f"Loaded {len(transformed_leads)} leads to {filepath}")
    logger.info(f"Master file now contains {len(combined_df)} total leads")

    return str(filepath)


@task
def generate_lead_insights(transformed_leads: pd.DataFrame) -> Dict:
    """Generate insights and metrics from lead data"""
    logger = get_run_logger()
    logger.info("Generating lead insights")

    insights = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_leads": len(transformed_leads),
        "conversion_rate": transformed_leads["converted"].mean(),
        "avg_deal_size": transformed_leads["deal_size_estimate"].mean(),
        "total_pipeline_value": transformed_leads["deal_size_estimate"].sum(),
        "high_quality_leads": (transformed_leads["lead_quality"] == "High").sum(),
        "top_industry": (
            transformed_leads["industry"].mode().iloc[0]
            if len(transformed_leads) > 0
            else None
        ),
        "top_region": (
            transformed_leads["region"].mode().iloc[0]
            if len(transformed_leads) > 0
            else None
        ),
        "avg_engagement_score": transformed_leads["engagement_score"].mean(),
        "decision_makers": transformed_leads["decision_maker"].sum(),
    }

    # Industry breakdown
    industry_breakdown = transformed_leads["industry"].value_counts().to_dict()
    insights["industry_breakdown"] = industry_breakdown

    # Company size breakdown
    size_breakdown = transformed_leads["company_size_category"].value_counts().to_dict()
    insights["size_breakdown"] = size_breakdown

    logger.info(
        f"Generated insights: {insights['total_leads']} leads, "
        f"{insights['conversion_rate']:.2%} conversion rate"
    )

    return insights


@task
def save_insights(insights: Dict, date: datetime):
    """Save insights to JSON file"""
    logger = get_run_logger()

    insights_dir = Path("data/insights")
    insights_dir.mkdir(parents=True, exist_ok=True)

    filepath = insights_dir / f"insights_{date.strftime('%Y%m%d')}.json"

    import json

    with open(filepath, "w") as f:
        json.dump(insights, f, indent=2, default=str)

    logger.info(f"Saved insights to {filepath}")


@flow(task_runner=SequentialTaskRunner())
def daily_lead_etl_pipeline(date: datetime = None, num_leads: int = 50):
    """Main ETL pipeline for daily lead processing"""
    if date is None:
        date = datetime.now()

    logger = get_run_logger()
    logger.info(f"Starting daily ETL pipeline for {date.strftime('%Y-%m-%d')}")

    try:
        # Extract
        raw_leads = extract_daily_leads(date, num_leads)

        # Transform
        transformed_leads = transform_leads(raw_leads)

        # Load
        filepath = load_leads_to_warehouse(transformed_leads, date)

        # Generate insights
        insights = generate_lead_insights(transformed_leads)
        save_insights(insights, date)

        logger.info("ETL pipeline completed successfully")
        return {
            "status": "success",
            "leads_processed": len(transformed_leads),
            "filepath": filepath,
            "insights": insights,
        }

    except Exception as e:
        logger.error(f"ETL pipeline failed: {str(e)}")
        return {"status": "error", "error": str(e)}


@flow
def backfill_historical_data(
    start_date: datetime, end_date: datetime, num_leads_per_day: int = 30
):
    """Backfill historical lead data for training"""
    logger = get_run_logger()
    logger.info(f"Starting backfill from {start_date} to {end_date}")

    current_date = start_date
    results = []

    while current_date <= end_date:
        logger.info(f"Processing {current_date.strftime('%Y-%m-%d')}")
        result = daily_lead_etl_pipeline(current_date, num_leads_per_day)
        results.append(result)
        current_date += timedelta(days=1)

    successful_runs = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Backfill completed: {successful_runs}/{len(results)} successful runs")

    return results


if __name__ == "__main__":
    # Run daily ETL pipeline
    result = daily_lead_etl_pipeline()
    print(f"ETL Result: {result}")

    # Uncomment to run backfill
    # start_date = datetime.now() - timedelta(days=30)
    # end_date = datetime.now()
    # backfill_results = backfill_historical_data(start_date, end_date)
    # print(f"Backfill completed: {len(backfill_results)} days processed")
