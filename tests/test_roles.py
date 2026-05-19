def test_consumer_cannot_train_model(client, consumer_headers):
    resp = client.post(
        "/api/v1/models/train",
        json={"dataset_uri": "data/synthetic_sensor_data.csv", "algorithm": "RandomForestClassifier"},
        headers=consumer_headers,
    )
    assert resp.status_code == 403


def test_ml_engineer_can_train_model(client, ml_engineer_headers):
    resp = client.post(
        "/api/v1/models/train",
        json={"dataset_uri": "data/synthetic_sensor_data.csv", "algorithm": "RandomForestClassifier"},
        headers=ml_engineer_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "metrics" in data


def test_ml_engineer_can_train_and_promote_flow(client, ml_engineer_headers):
    resp = client.post(
        "/api/v1/models/train-and-promote",
        json={"dataset_uri": "data/synthetic_sensor_data.csv", "algorithm": "RandomForestClassifier"},
        headers=ml_engineer_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert "model_id" in data
    assert isinstance(data["promoted"], bool)
    assert "promotion_reason" in data
    assert "metrics" in data



def test_ml_engineer_can_get_run_detail(client, ml_engineer_headers):
    created = client.post(
        "/api/v1/models/train-and-promote",
        json={"dataset_uri": "data/synthetic_sensor_data.csv", "algorithm": "RandomForestClassifier"},
        headers=ml_engineer_headers,
    )
    run_id = created.json()["run_id"]

    detail = client.get(f"/api/v1/models/runs/{run_id}", headers=ml_engineer_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["run_id"] == run_id
    assert body["status"] == "completed"
    assert body["model_version"]


def test_run_detail_not_found(client, ml_engineer_headers):
    detail = client.get("/api/v1/models/runs/not-found", headers=ml_engineer_headers)
    assert detail.status_code == 404


def test_admin_can_get_run_detail_and_not_found(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin_run@example.com", "password": "StrongPassword123!", "role": "admin"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_run@example.com", "password": "StrongPassword123!"},
    )
    assert login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    created = client.post(
        "/api/v1/models/train-and-promote",
        json={"dataset_uri": "data/synthetic_sensor_data.csv", "algorithm": "RandomForestClassifier"},
        headers=admin_headers,
    )
    assert created.status_code == 200
    run_id = created.json()["run_id"]

    detail = client.get(f"/api/v1/models/runs/{run_id}", headers=admin_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["run_id"] == run_id
    assert body["status"] == "completed"
    assert body["model_version"]

    not_found = client.get("/api/v1/models/runs/not-found", headers=admin_headers)
    assert not_found.status_code == 404


def test_models_current_requires_auth(client):
    resp = client.get("/api/v1/models/current")
    assert resp.status_code == 401
