PAYLOAD = {
    "asset_code": "PUMP-001",
    "temperature": 91.5,
    "pressure": 7.8,
    "vibration": 0.82,
    "flow_rate": 120.4,
    "energy_consumption": 430.2,
    "operating_hours": 5020,
}


def test_predict_requires_jwt(client):
    resp = client.post("/api/v1/predict", json=PAYLOAD)
    assert resp.status_code == 401


def test_predict_with_auth_success(client, consumer_headers):
    resp = client.post("/api/v1/predict", json=PAYLOAD, headers=consumer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "prediction_id" in data
    assert data["risk_level"] in ["low", "medium", "high"]
    assert 0 <= data["failure_probability"] <= 1
    assert "model_version" in data


def test_predict_validation_pydantic_422(client, consumer_headers):
    bad_payload = dict(PAYLOAD)
    bad_payload["pressure"] = 0
    resp = client.post("/api/v1/predict", json=bad_payload, headers=consumer_headers)
    assert resp.status_code == 422


def test_predict_rejects_negative_energy(client, consumer_headers):
    bad_payload = dict(PAYLOAD)
    bad_payload["energy_consumption"] = -1
    resp = client.post("/api/v1/predict", json=bad_payload, headers=consumer_headers)
    assert resp.status_code == 422
