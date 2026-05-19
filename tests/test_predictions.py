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
