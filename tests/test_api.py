"""Tests for the lead-scoring API. The predict_single test reproduces the
exact request from the README that used to crash with a 500 error
(prepare_features blanket-filled missing categorical fields with 0 instead
of "Unknown", which broke the one-hot encoder)."""

import pytest
from fastapi.testclient import TestClient

from api.enhanced_main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["model_loaded"] is True


def test_predict_single_with_minimal_fields(client):
    """This is the exact request from the README's quickstart example."""
    response = client.post(
        "/predict/single",
        json={
            "company_name": "TechCorp Inc.",
            "email": "contact@techcorp.com",
            "industry": "Technology",
            "company_size": "51-200",
            "region": "NA",
            "deal_size_estimate": 50000,
            "page_views_7d": 15,
            "emails_opened_30d": 8,
            "calls_last_30d": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["conversion_probability"] <= 1
    assert body["revenue_impact"] >= 0
    assert body["next_best_action"] in {"Call", "Email", "Nurture"}


def test_predict_batch(client):
    response = client.post(
        "/predict/batch",
        json={
            "leads": [
                {
                    "company_name": "Company A",
                    "email": "contact@companya.com",
                    "industry": "Finance",
                    "company_size": "201-1000",
                    "region": "EU",
                    "deal_size_estimate": 25000,
                    "page_views_7d": 10,
                    "emails_opened_30d": 5,
                    "calls_last_30d": 1,
                }
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_leads"] == 1


def test_top_leads(client):
    response = client.get("/predict/top-leads", params={"limit": 3})
    assert response.status_code == 200
    leads = response.json()["leads"]
    assert len(leads) == 3
    # sorted descending by revenue impact
    impacts = [lead["revenue_impact"] for lead in leads]
    assert impacts == sorted(impacts, reverse=True)


def test_leads_list_and_search(client):
    response = client.get("/leads", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert len(body["leads"]) == 5


def test_analytics_summary(client):
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    for key in [
        "totalLeads",
        "conversionRate",
        "totalRevenue",
        "highPriorityLeads",
        "industryBreakdown",
        "monthlyTrend",
    ]:
        assert key in body


def test_chatbot_query(client):
    response = client.post("/chatbot/query", json={"message": "who are my top leads"})
    assert response.status_code == 200
    assert "response" in response.json()
