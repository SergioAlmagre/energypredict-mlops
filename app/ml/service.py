from __future__ import annotations

from typing import Any, Dict

from app.ml.registry import get_current_model_metadata, list_training_runs_data, promote_model
from app.ml.registry import list_drift_reports_data
from app.ml.train import train_model


def train_model_service(payload: Dict[str, Any] | None = None, *args, **kwargs) -> Dict[str, Any]:
    if args:
        dataset_uri = payload if isinstance(payload, str) else args[0]
        algorithm = args[0] if isinstance(payload, str) else "RandomForestClassifier"
        register_model = args[1] if len(args) > 1 else True
        return train_model(dataset_uri=dataset_uri, algorithm=algorithm, register_model=register_model)

    data = payload or {}
    dataset_uri = kwargs.get("dataset_uri", data.get("dataset_uri", "data/synthetic_sensor_data.csv"))
    algorithm = kwargs.get("algorithm", data.get("algorithm", "RandomForestClassifier"))
    register_model = kwargs.get("register_model", data.get("register_model", True))
    return train_model(dataset_uri=dataset_uri, algorithm=algorithm, register_model=register_model)


def get_current_model() -> Dict[str, Any]:
    return get_current_model_metadata()


def list_training_runs() -> list[Dict[str, Any]]:
    return list_training_runs_data()


def list_drift_reports() -> list[Dict[str, Any]]:
    return list_drift_reports_data()


def promote_model_to_production(model_id: str) -> Dict[str, Any]:
    return promote_model(model_id=model_id, target_stage="production")
