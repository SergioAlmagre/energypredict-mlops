from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.models import User
from app.db.session import get_db
from app.schemas.prediction import RiskThresholdResponse, RiskThresholdUpdateRequest
from app.schemas.streaming import SimulationControlResponse
from app.services.risk_policy_service import get_or_create_active_policy, update_active_thresholds
from app.services.streaming_service import get_or_create_simulation_state, set_simulation_running

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/risk-thresholds", response_model=RiskThresholdResponse)
def get_risk_thresholds(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    policy = get_or_create_active_policy(db)
    return RiskThresholdResponse(
        low_max=policy.low_max,
        medium_max=policy.medium_max,
        updated_by_user_id=policy.updated_by_user_id,
        updated_at=policy.updated_at,
    )


@router.put("/risk-thresholds", response_model=RiskThresholdResponse)
def update_risk_thresholds(
    payload: RiskThresholdUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    policy = update_active_thresholds(
        db=db,
        changed_by_user_id=current_user.id,
        low_max=payload.low_max,
        medium_max=payload.medium_max,
    )
    return RiskThresholdResponse(
        low_max=policy.low_max,
        medium_max=policy.medium_max,
        updated_by_user_id=policy.updated_by_user_id,
        updated_at=policy.updated_at,
    )


@router.get("/simulation/status", response_model=SimulationControlResponse)
def get_simulation_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    state = get_or_create_simulation_state(db)
    return SimulationControlResponse(
        is_running=state.is_running,
        last_started_at=state.last_started_at,
        last_stopped_at=state.last_stopped_at,
        updated_by_user_id=state.updated_by_user_id,
        updated_at=state.updated_at,
    )


@router.post("/simulation/start", response_model=SimulationControlResponse)
def start_simulation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    state = set_simulation_running(db, running=True, updated_by_user_id=current_user.id)
    return SimulationControlResponse(
        is_running=state.is_running,
        last_started_at=state.last_started_at,
        last_stopped_at=state.last_stopped_at,
        updated_by_user_id=state.updated_by_user_id,
        updated_at=state.updated_at,
    )


@router.post("/simulation/stop", response_model=SimulationControlResponse)
def stop_simulation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    state = set_simulation_running(db, running=False, updated_by_user_id=current_user.id)
    return SimulationControlResponse(
        is_running=state.is_running,
        last_started_at=state.last_started_at,
        last_stopped_at=state.last_stopped_at,
        updated_by_user_id=state.updated_by_user_id,
        updated_at=state.updated_at,
    )
