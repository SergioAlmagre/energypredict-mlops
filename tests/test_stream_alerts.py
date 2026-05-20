from app.services.risk_policy_service import update_active_thresholds
from app.services.streaming_service import ingest_telemetry_event
from conftest import TestingSessionLocal


def _sample_payload(asset_code: str) -> dict:
    return {
        "asset_code": asset_code,
        "temperature": 97.2,
        "pressure": 8.3,
        "vibration": 6.8,
        "flow_rate": 41.7,
        "energy_consumption": 498.4,
        "operating_hours": 9042,
    }


def test_stream_latest_requires_token(client):
    response = client.get("/api/v1/stream/latest")
    assert response.status_code == 401


def test_stream_latest_and_active_alerts_return_data(client, consumer_headers):
    with TestingSessionLocal() as db:
        update_active_thresholds(db=db, changed_by_user_id=None, low_max=0.0, medium_max=0.01)
        ingest_telemetry_event(db, telemetry=_sample_payload("PUMP-777"), source="test")

    stream_response = client.get("/api/v1/stream/latest?limit=10", headers=consumer_headers)
    assert stream_response.status_code == 200
    stream_items = stream_response.json()
    assert any(item["asset_code"] == "PUMP-777" for item in stream_items)

    alerts_response = client.get("/api/v1/alerts/active?limit=10", headers=consumer_headers)
    assert alerts_response.status_code == 200
    active_alerts = alerts_response.json()
    assert any(alert["asset_code"] == "PUMP-777" for alert in active_alerts)


def test_stream_ingestion_persists_prediction_explanation_row():
    from app.db.models import PredictionExplanation, SensorEvent

    with TestingSessionLocal() as db:
        update_active_thresholds(db=db, changed_by_user_id=None, low_max=0.0, medium_max=0.01)
        event = ingest_telemetry_event(
            db,
            telemetry=_sample_payload("PUMP-888"),
            source="test",
            trace_id="trace-stream-888",
        )
        db_event = db.query(SensorEvent).filter(SensorEvent.id == event.id).first()
        assert db_event is not None
        explanation = (
            db.query(PredictionExplanation)
            .filter(PredictionExplanation.sensor_event_id == event.id)
            .first()
        )
        assert explanation is not None
        assert explanation.trace_id == "trace-stream-888"
        assert explanation.explanation_text


def test_stream_and_alerts_support_asset_code_filter(client, consumer_headers):
    with TestingSessionLocal() as db:
        update_active_thresholds(db=db, changed_by_user_id=None, low_max=0.0, medium_max=0.01)
        ingest_telemetry_event(db, telemetry=_sample_payload("PUMP-101"), source="test")
        ingest_telemetry_event(db, telemetry=_sample_payload("PUMP-202"), source="test")

    stream_filtered = client.get(
        "/api/v1/stream/latest?asset_code=PUMP-101&limit=10",
        headers=consumer_headers,
    )
    assert stream_filtered.status_code == 200
    stream_items = stream_filtered.json()
    assert len(stream_items) > 0
    assert all(item["asset_code"] == "PUMP-101" for item in stream_items)

    alerts_filtered = client.get(
        "/api/v1/alerts/active?asset_code=PUMP-202&limit=10",
        headers=consumer_headers,
    )
    assert alerts_filtered.status_code == 200
    alert_items = alerts_filtered.json()
    assert len(alert_items) > 0
    assert all(item["asset_code"] == "PUMP-202" for item in alert_items)
