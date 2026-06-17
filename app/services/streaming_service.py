from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.metrics import observe_active_alerts, observe_prediction
from app.db.models import Alert, SensorEvent, SimulationControlState
from app.schemas.prediction import PredictionRequest
from app.services.llm_explainer_service import build_operations_explanation
from app.services.prediction_service import get_or_create_production_model, persist_prediction_explanation
from app.services.risk_policy_service import get_active_thresholds
from app.ml.predict import predict_failure_risk


def get_or_create_simulation_state(db: Session) -> SimulationControlState:
    state = db.query(SimulationControlState).first()
    if state:
        return state

    state = SimulationControlState(is_running=False)
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def set_simulation_running(db: Session, running: bool, updated_by_user_id: str | None) -> SimulationControlState:
    now = datetime.now(timezone.utc)
    state = get_or_create_simulation_state(db)
    state.is_running = running
    state.updated_by_user_id = updated_by_user_id
    if running:
        state.last_started_at = now
    else:
        state.last_stopped_at = now
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def ingest_telemetry_event(
    db: Session,
    telemetry: dict,
    source: str = "simulation",
    trace_id: str = "n/a",
) -> SensorEvent:
    payload = PredictionRequest(**telemetry).model_dump()
    thresholds = get_active_thresholds(db)
    inference = predict_failure_risk(
        payload,
        low_max=thresholds.low_max,
        medium_max=thresholds.medium_max,
    )
    model = get_or_create_production_model(db)
    explanation = build_operations_explanation(
        payload=payload,
        failure_probability=inference["failure_probability"],
        risk_level=inference["risk_level"],
        trace_id=trace_id,
    )
    event = SensorEvent(
        asset_code=payload["asset_code"],
        source=source,
        event_ts=datetime.now(timezone.utc),
        telemetry_payload=payload,
        model_version_id=model.id,
        risk_level=inference["risk_level"],
        failure_probability=inference["failure_probability"],
        recommendation=explanation.recommendation,
    )
    db.add(event)
    db.flush()
    persist_prediction_explanation(
        db=db,
        prediction_id=None,
        sensor_event_id=event.id,
        provider=explanation.provider,
        model=explanation.model,
        prompt_version=explanation.prompt_version,
        model_version_id=model.id,
        notes=explanation.notes,
        explanation_text=explanation.recommendation,
        trace_id=trace_id,
        auto_commit=False,
    )
    _upsert_alert_for_event(db=db, event=event)
    db.commit()
    db.refresh(event)
    observe_prediction(source=source, risk_level=event.risk_level, model_version=model.version)
    observe_active_alerts(_active_alert_counts(db))
    return event


def list_latest_events(db: Session, limit: int = 20, asset_code: str | None = None) -> list[SensorEvent]:
    safe_limit = max(1, min(limit, 200))
    query = db.query(SensorEvent)
    if asset_code:
        query = query.filter(SensorEvent.asset_code == asset_code)
    return query.order_by(SensorEvent.event_ts.desc()).limit(safe_limit).all()


def list_active_alerts(db: Session, limit: int = 50, asset_code: str | None = None) -> list[Alert]:
    safe_limit = max(1, min(limit, 200))
    query = db.query(Alert).filter(Alert.status == "active")
    if asset_code:
        query = query.filter(Alert.asset_code == asset_code)
    return query.order_by(Alert.updated_at.desc()).limit(safe_limit).all()


def _upsert_alert_for_event(db: Session, event: SensorEvent) -> None:
    active = (
        db.query(Alert)
        .filter(Alert.asset_code == event.asset_code, Alert.status == "active")
        .first()
    )
    now = datetime.now(timezone.utc)

    if event.risk_level == "low":
        if active:
            active.status = "resolved"
            active.resolved_at = now
            active.updated_at = now
            db.add(active)
        return

    severity = "high" if event.risk_level == "high" else "medium"
    if active:
        active.sensor_event_id = event.id
        active.severity = severity
        active.failure_probability = event.failure_probability
        active.message = event.recommendation
        active.updated_at = now
        db.add(active)
        return

    db.add(
        Alert(
            asset_code=event.asset_code,
            sensor_event_id=event.id,
            severity=severity,
            status="active",
            failure_probability=event.failure_probability,
            message=event.recommendation,
            created_at=now,
            updated_at=now,
        )
    )


def _active_alert_counts(db: Session) -> dict[str, int]:
    counts = {"medium": 0, "high": 0}
    active_alerts = db.query(Alert).filter(Alert.status == "active").all()
    for alert in active_alerts:
        if alert.severity in counts:
            counts[alert.severity] += 1
    return counts
