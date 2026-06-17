from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import joblib

from app.core.config import get_settings
from app.integrations.blob_storage import download_file_uri, is_blob_configured, read_json, write_json

MODELS_DIR = Path("models")
REGISTRY_PATH = MODELS_DIR / "registry.json"
REGISTRY_BLOB_NAME = "registry.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_registry() -> Dict[str, Any]:
    return {"models": [], "production_model_id": None, "training_runs": [], "drift_reports": []}


def load_registry() -> Dict[str, Any]:
    settings = get_settings()
    if settings.model_registry_backend == "blob" and is_blob_configured():
        registry = read_json(settings.blob_registry_container, REGISTRY_BLOB_NAME)
        if registry:
            return registry
    if not REGISTRY_PATH.exists():
        return _default_registry()
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(registry: Dict[str, Any]) -> None:
    settings = get_settings()
    if settings.model_registry_backend == "blob" and is_blob_configured():
        write_json(settings.blob_registry_container, REGISTRY_BLOB_NAME, registry)
        return
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def register_model(metadata: Dict[str, Any]) -> Dict[str, Any]:
    registry = load_registry()
    if metadata.get("stage") == "production":
        metadata["mlflow_alias_sync"] = _sync_mlflow_production_alias(metadata)
    registry["models"].append(metadata)
    if metadata.get("stage") == "production":
        registry["production_model_id"] = metadata["model_id"]
    save_registry(registry)
    return metadata


def register_training_run(run: Dict[str, Any]) -> Dict[str, Any]:
    registry = load_registry()
    registry["training_runs"].append(run)
    save_registry(registry)
    return run


def update_training_run(run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    registry = load_registry()
    for run in registry["training_runs"]:
        if run["run_id"] == run_id:
            run.update(updates)
            save_registry(registry)
            return run
    raise ValueError(f"Run not found: {run_id}")


def list_training_runs_data() -> List[Dict[str, Any]]:
    return load_registry().get("training_runs", [])


def list_models() -> List[Dict[str, Any]]:
    return load_registry().get("models", [])


def register_drift_report(report: Dict[str, Any]) -> Dict[str, Any]:
    registry = load_registry()
    registry.setdefault("drift_reports", []).append(report)
    save_registry(registry)
    return report


def list_drift_reports_data() -> List[Dict[str, Any]]:
    return load_registry().get("drift_reports", [])


def get_current_model_metadata() -> Dict[str, Any]:
    registry = load_registry()
    prod_id = registry.get("production_model_id")
    if prod_id:
        for model in registry.get("models", []):
            if model["model_id"] == prod_id:
                return model
    models = registry.get("models", [])
    if not models:
        raise FileNotFoundError("No models are registered yet")
    return models[-1]


def load_current_model():
    metadata = get_current_model_metadata()
    model_path = download_file_uri(metadata["artifact_uri"])
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {model_path}")
    return joblib.load(model_path), metadata


def promote_model(model_id: str, target_stage: str = "production") -> Dict[str, Any]:
    if target_stage != "production":
        raise ValueError("Only promotion to production is supported in MVP")

    registry = load_registry()
    models = registry.get("models", [])
    target_model = None

    for model in models:
        if model.get("stage") == "production":
            model["stage"] = "archived"
        if model["model_id"] == model_id:
            target_model = model

    if not target_model:
        raise ValueError(f"Model not found: {model_id}")

    target_model["stage"] = "production"
    target_model["promoted_at"] = _now_iso()
    target_model["mlflow_alias_sync"] = _sync_mlflow_production_alias(target_model)
    registry["production_model_id"] = model_id
    save_registry(registry)
    return target_model


def _sync_mlflow_production_alias(model: Dict[str, Any]) -> Dict[str, Any]:
    registered_model_name = model.get("mlflow_registered_model_name")
    registered_model_version = model.get("mlflow_registered_model_version")
    if not registered_model_name or not registered_model_version:
        return {"status": "skipped", "reason": "Missing MLflow registered model name or version."}

    from app.integrations.mlflow_client import MLflowClient

    return MLflowClient().set_production_alias(
        registered_model_name=registered_model_name,
        registered_model_version=str(registered_model_version),
    )
