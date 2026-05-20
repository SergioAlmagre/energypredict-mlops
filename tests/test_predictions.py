def test_predict_requires_token(client):
    payload = {
        "asset_code": "PUMP-001",
        "temperature": 91.5,
        "pressure": 7.8,
        "vibration": 0.82,
        "flow_rate": 120.4,
        "energy_consumption": 430.2,
        "operating_hours": 5020,
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 401


def test_predict_with_valid_token_and_persistence(client):
    client.post("/api/v1/auth/register", json={"email": "predict_user@example.com", "password": "StrongPassword123!", "role": "consumer"})
    login_resp = client.post("/api/v1/auth/login", data={"username": "predict_user@example.com", "password": "StrongPassword123!"})
    token = login_resp.json()["access_token"]

    payload = {
        "asset_code": "PUMP-001",
        "temperature": 91.5,
        "pressure": 7.8,
        "vibration": 0.82,
        "flow_rate": 120.4,
        "energy_consumption": 430.2,
        "operating_hours": 5020,
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/predict", json=payload, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["asset_code"] == "PUMP-001"
    assert body["risk_level"] in ["low", "medium", "high"]
    assert 0 <= body["failure_probability"] <= 1
    assert body["prediction_id"]


def test_predict_risk_level_changes_when_admin_updates_thresholds(client, consumer_headers, admin_headers):
    payload = {
        "asset_code": "PUMP-009",
        "temperature": 82.0,
        "pressure": 7.1,
        "vibration": 4.4,
        "flow_rate": 24.5,
        "energy_consumption": 356.7,
        "operating_hours": 2150,
    }

    baseline = client.post("/api/v1/predict", json=payload, headers=consumer_headers)
    assert baseline.status_code == 200
    baseline_body = baseline.json()

    update = client.put(
        "/api/v1/admin/risk-thresholds",
        json={"low_max": 0.9, "medium_max": 0.95},
        headers=admin_headers,
    )
    assert update.status_code == 200

    after_update = client.post("/api/v1/predict", json=payload, headers=consumer_headers)
    assert after_update.status_code == 200
    updated_body = after_update.json()

    assert 0 <= baseline_body["failure_probability"] <= 1
    assert 0 <= updated_body["failure_probability"] <= 1
    assert updated_body["risk_level"] == "low"


def test_predict_uses_llm_recommendation_when_available(client, consumer_headers, monkeypatch):
    from app.services import prediction_service
    from app.services.llm_explainer_service import LLMExplanationResult

    monkeypatch.setattr(
        prediction_service,
        "build_operations_explanation",
        lambda payload, failure_probability, risk_level, trace_id="n/a": LLMExplanationResult(
            recommendation="LLM custom recommendation",
            provider="openai-compatible",
            model="test-model",
            prompt_version="v1",
            notes=None,
        ),
    )

    payload = {
        "asset_code": "PUMP-777",
        "temperature": 90.0,
        "pressure": 6.8,
        "vibration": 3.1,
        "flow_rate": 25.0,
        "energy_consumption": 301.0,
        "operating_hours": 1880,
    }

    response = client.post("/api/v1/predict", json=payload, headers=consumer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["recommendation"] == "LLM custom recommendation"


def test_predict_persists_prediction_explanation_row(client, consumer_headers):
    from app.db.models import PredictionExplanation
    from conftest import TestingSessionLocal

    payload = {
        "asset_code": "PUMP-888",
        "temperature": 84.2,
        "pressure": 7.2,
        "vibration": 2.9,
        "flow_rate": 30.0,
        "energy_consumption": 320.0,
        "operating_hours": 2100,
    }
    response = client.post("/api/v1/predict", json=payload, headers=consumer_headers)
    assert response.status_code == 200
    prediction_id = response.json()["prediction_id"]

    with TestingSessionLocal() as db:
        row = db.query(PredictionExplanation).filter(PredictionExplanation.prediction_id == prediction_id).first()

    assert row is not None
    assert row.trace_id is not None
    assert row.prompt_version == "v1"
    assert row.explanation_text


def test_predict_persists_custom_trace_id_into_explanation(client, consumer_headers):
    from app.db.models import PredictionExplanation
    from conftest import TestingSessionLocal

    trace_id = "trace-e2e-12345"
    payload = {
        "asset_code": "PUMP-889",
        "temperature": 85.1,
        "pressure": 7.0,
        "vibration": 2.8,
        "flow_rate": 28.0,
        "energy_consumption": 315.0,
        "operating_hours": 2200,
    }
    headers = dict(consumer_headers)
    headers["X-Trace-Id"] = trace_id
    response = client.post("/api/v1/predict", json=payload, headers=headers)
    assert response.status_code == 200
    prediction_id = response.json()["prediction_id"]

    with TestingSessionLocal() as db:
        row = db.query(PredictionExplanation).filter(PredictionExplanation.prediction_id == prediction_id).first()

    assert row is not None
    assert row.trace_id == trace_id
