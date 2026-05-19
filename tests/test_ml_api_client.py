from __future__ import annotations

import httpx
import pytest

from app.integrations.ml_api_client import MLApiClient, MLApiClientError


def _transport_ok(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/v1/models/current":
        return httpx.Response(200, json={"name": "asset_failure_classifier", "version": "1.0.0", "stage": "production"})
    if request.url.path == "/api/v1/models/train":
        return httpx.Response(200, json={"run_id": "r1", "status": "completed", "metrics": {"accuracy": 0.9}, "model": {"model_id": "m1"}})
    if request.url.path == "/api/v1/models/runs":
        return httpx.Response(200, json={"items": [{"run_id": "r1", "status": "completed"}]})
    if request.url.path == "/api/v1/models/m1/promote":
        return httpx.Response(200, json={"model_id": "m1", "stage": "production"})
    if request.url.path == "/api/v1/predict":
        return httpx.Response(200, json={"failure_probability": 0.88, "risk_level": "high", "model_version": "1.0.0"})
    return httpx.Response(404, json={"detail": "not found"})


def _transport_error(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(500, json={"detail": "boom"})


def test_ml_api_client_happy_path():
    client = httpx.Client(transport=httpx.MockTransport(_transport_ok))
    api = MLApiClient(base_url="http://backend.local/api/v1", token="tkn", client=client)

    current = api.get_current_model()
    assert current["stage"] == "production"

    trained = api.train_model({"dataset_uri": "data/synthetic_sensor_data.csv"})
    assert trained["status"] == "completed"

    runs = api.list_runs()
    assert len(runs["items"]) == 1

    promoted = api.promote_model("m1")
    assert promoted["stage"] == "production"

    pred = api.predict_failure_risk(
        {
            "asset_code": "PUMP-001",
            "temperature": 91.5,
            "pressure": 7.8,
            "vibration": 0.82,
            "flow_rate": 120.4,
            "energy_consumption": 430.2,
            "operating_hours": 5020,
        }
    )
    assert pred["risk_level"] == "high"


def test_ml_api_client_raises_on_error():
    client = httpx.Client(transport=httpx.MockTransport(_transport_error))
    api = MLApiClient(base_url="http://backend.local/api/v1", token="tkn", client=client)

    with pytest.raises(MLApiClientError):
        api.get_current_model()
