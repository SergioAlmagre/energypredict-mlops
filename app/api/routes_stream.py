from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.models import User
from app.db.session import get_db
from app.schemas.streaming import SensorEventResponse
from app.services.streaming_service import list_latest_events

router = APIRouter(tags=["stream"])


@router.get("/stream/latest", response_model=list[SensorEventResponse])
def get_latest_stream_events(
    limit: int = Query(default=20, ge=1, le=200),
    asset_code: str | None = Query(default=None, min_length=1, max_length=120),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("consumer", "analyst", "ml_engineer", "admin")),
):
    events = list_latest_events(db, limit=limit, asset_code=asset_code)
    return [
        SensorEventResponse(
            id=event.id,
            asset_code=event.asset_code,
            source=event.source,
            event_ts=event.event_ts,
            telemetry_payload=event.telemetry_payload,
            risk_level=event.risk_level,  # type: ignore[arg-type]
            failure_probability=event.failure_probability,
            recommendation=event.recommendation,
            created_at=event.created_at,
        )
        for event in events
    ]
