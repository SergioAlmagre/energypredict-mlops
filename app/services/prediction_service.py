from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ModelVersion, Prediction, PredictionExplanation, User
from app.ml.predict import predict_failure_risk
from app.ml.service import get_current_model
from app.schemas.prediction import PredictionRequest
from app.services.llm_explainer_service import build_operations_explanation
from app.services.risk_policy_service import get_active_thresholds


def get_or_create_production_model(db: Session) -> ModelVersion:
    settings = get_settings()
    try:
        current_model = get_current_model()
    except Exception:
        current_model = None

    model = (
        db.query(ModelVersion)
        .filter(ModelVersion.name == settings.default_model_name, ModelVersion.stage == "production")
        .first()
    )
    if model:
        if current_model and model.version != current_model.get("version"):
            model.version = current_model["version"]
            model.algorithm = current_model.get("algorithm", model.algorithm)
            db.add(model)
            db.commit()
            db.refresh(model)
        return model

    model = ModelVersion(
        name=settings.default_model_name,
        version=current_model["version"] if current_model else settings.default_model_version,
        stage="production",
        algorithm=current_model.get("algorithm", "HeuristicBaseline") if current_model else "HeuristicBaseline",
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def create_prediction(db: Session, payload: PredictionRequest, current_user: User, trace_id: str = "n/a") -> tuple[Prediction, ModelVersion]:
    thresholds = get_active_thresholds(db)
    inference = predict_failure_risk(
        payload.model_dump(),
        low_max=thresholds.low_max,
        medium_max=thresholds.medium_max,
    )
    model = get_or_create_production_model(db)
    explanation = build_operations_explanation(
        payload=payload.model_dump(),
        failure_probability=inference["failure_probability"],
        risk_level=inference["risk_level"],
        trace_id=trace_id,
    )

    prediction = Prediction(
        user_id=current_user.id,
        model_version_id=model.id,
        asset_code=payload.asset_code,
        input_payload=payload.model_dump(),
        risk_level=inference["risk_level"],
        failure_probability=inference["failure_probability"],
        recommendation=explanation.recommendation,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    persist_prediction_explanation(
        db=db,
        prediction_id=prediction.id,
        sensor_event_id=None,
        provider=explanation.provider,
        model=explanation.model,
        prompt_version=explanation.prompt_version,
        model_version_id=model.id,
        notes=explanation.notes,
        explanation_text=explanation.recommendation,
        trace_id=trace_id,
    )
    return prediction, model


def persist_prediction_explanation(
    db: Session,
    prediction_id: str | None,
    sensor_event_id: str | None,
    provider: str,
    model: str,
    prompt_version: str,
    model_version_id: str | None,
    notes: str | None,
    explanation_text: str,
    trace_id: str,
    auto_commit: bool = True,
) -> PredictionExplanation:
    explanation_row = PredictionExplanation(
        prediction_id=prediction_id,
        sensor_event_id=sensor_event_id,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        model_version_id=model_version_id,
        notes=notes,
        explanation_text=explanation_text,
        trace_id=trace_id,
    )
    db.add(explanation_row)
    if auto_commit:
        db.commit()
    else:
        db.flush()
    db.refresh(explanation_row)
    return explanation_row
