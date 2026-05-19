from __future__ import annotations

import pandas as pd

from app.ml.features import build_features
from app.ml.registry import load_current_model
from app.schemas.prediction import PredictionRequest


def risk_level_from_probability(probability: float) -> str:
    if probability < 0.35:
        return "low"
    if probability < 0.70:
        return "medium"
    return "high"


def _as_request(payload: PredictionRequest | dict) -> PredictionRequest:
    if isinstance(payload, PredictionRequest):
        return payload
    return PredictionRequest(**payload)


def predict_failure_risk(payload: PredictionRequest | dict) -> dict:
    payload = _as_request(payload)
    model_probability = _predict_with_active_model(payload)
    if model_probability is not None:
        probability = model_probability
    else:
        probability = _heuristic_probability(payload)

    risk_level = risk_level_from_probability(probability)

    if risk_level == "low":
        recommendation = "Keep normal maintenance schedule."
    elif risk_level == "medium":
        recommendation = "Schedule preventive inspection in the next 7 days."
    else:
        recommendation = "Inspect asset within 24 hours and review vibration trend."

    return {
        "failure_probability": probability,
        "risk_level": risk_level,
        "recommendation": recommendation,
    }


def _predict_with_active_model(payload: PredictionRequest) -> float | None:
    try:
        model, _metadata = load_current_model()
    except Exception:
        return None

    payload_df = pd.DataFrame([payload.model_dump()])
    featured = build_features(payload_df)
    features = featured.drop(columns=["asset_code"], errors="ignore")

    if not hasattr(model, "predict_proba"):
        return None

    try:
        probability = float(model.predict_proba(features)[0][1])
    except Exception:
        return None
    return max(0.0, min(probability, 1.0))


def _heuristic_probability(payload: PredictionRequest) -> float:
    score = (
        (payload.temperature / 250) * 0.25
        + (payload.pressure / 500) * 0.15
        + (payload.vibration / 50) * 0.2
        + min(payload.energy_consumption / 1000, 1.0) * 0.2
        + min(payload.operating_hours / 10000, 1.0) * 0.2
    )
    return max(0.0, min(score, 1.0))
