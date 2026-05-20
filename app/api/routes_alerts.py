from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.models import User
from app.db.session import get_db
from app.schemas.streaming import ActiveAlertResponse
from app.services.streaming_service import list_active_alerts

router = APIRouter(tags=["alerts"])


@router.get("/alerts/active", response_model=list[ActiveAlertResponse])
def get_active_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    asset_code: str | None = Query(default=None, min_length=1, max_length=120),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("consumer", "analyst", "ml_engineer", "admin")),
):
    alerts = list_active_alerts(db, limit=limit, asset_code=asset_code)
    return [
        ActiveAlertResponse(
            id=alert.id,
            asset_code=alert.asset_code,
            sensor_event_id=alert.sensor_event_id,
            severity=alert.severity,  # type: ignore[arg-type]
            status=alert.status,  # type: ignore[arg-type]
            failure_probability=alert.failure_probability,
            message=alert.message,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
        for alert in alerts
    ]
