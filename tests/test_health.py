def test_health_live_ok(client):
    resp = client.get("/api/v1/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_ready_ok(client, monkeypatch):
    from app.api import routes_health

    def current_model():
        return {"name": "asset_failure_classifier", "version": "test-version", "stage": "production"}

    monkeypatch.setattr(routes_health, "get_current_model_metadata", current_model)
    resp = client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert data["model"] == "ok"


def test_health_ready_reports_missing_model(client, monkeypatch):
    from app.api import routes_health

    def missing_model():
        raise FileNotFoundError("No models are registered yet")

    monkeypatch.setattr(routes_health, "get_current_model_metadata", missing_model)
    resp = client.get("/api/v1/health/ready")

    assert resp.status_code == 503
    assert resp.json()["detail"] == {
        "status": "not_ready",
        "database": "ok",
        "model": "unavailable",
        "reason": "no_production_model_registered",
    }


def test_health_ready_reports_registry_backend_unreachable(client, monkeypatch):
    from app.api import routes_health
    from app.integrations.blob_storage import BlobStorageUnavailable

    def blob_unavailable():
        raise BlobStorageUnavailable("Azure Storage is not configured")

    monkeypatch.setattr(routes_health, "get_current_model_metadata", blob_unavailable)
    resp = client.get("/api/v1/health/ready")

    assert resp.status_code == 503
    assert resp.json()["detail"]["reason"] == "registry_backend_unreachable"
