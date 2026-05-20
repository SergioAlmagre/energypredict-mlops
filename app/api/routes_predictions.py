from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limit_by_ip
from app.core.security import require_roles
from app.db.models import User
from app.db.session import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import create_prediction

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict(
    payload: PredictionRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(
        limit_by_ip(
            scope="predict",
            limit=get_settings().predict_rate_limit_requests,
            window_seconds=get_settings().predict_rate_limit_window_seconds,
        )
    ),
    current_user: User = Depends(require_roles("consumer", "analyst", "ml_engineer", "admin")),
):
    prediction, model = create_prediction(
        db,
        payload,
        current_user,
        trace_id=request.headers.get("X-Trace-Id", "n/a"),
    )
    return PredictionResponse(
        prediction_id=prediction.id,
        asset_code=prediction.asset_code,
        risk_level=prediction.risk_level,
        failure_probability=prediction.failure_probability,
        recommendation=prediction.recommendation,
        model_name=model.name,
        model_version=model.version,
        created_at=prediction.created_at,
    )
