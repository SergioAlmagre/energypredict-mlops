from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ModelVersion, Prediction, User
from app.ml.predict import predict_failure_risk
from app.ml.service import get_current_model
from app.schemas.prediction import PredictionRequest


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


def create_prediction(db: Session, payload: PredictionRequest, current_user: User) -> tuple[Prediction, ModelVersion]:
    inference = predict_failure_risk(payload.model_dump())
    model = get_or_create_production_model(db)

    prediction = Prediction(
        user_id=current_user.id,
        model_version_id=model.id,
        asset_code=payload.asset_code,
        input_payload=payload.model_dump(),
        risk_level=inference["risk_level"],
        failure_probability=inference["failure_probability"],
        recommendation=inference["recommendation"],
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction, model
