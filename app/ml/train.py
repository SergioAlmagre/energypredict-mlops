from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier

from app.core.config import get_settings
from app.integrations.blob_storage import is_blob_configured, upload_file
from app.integrations.mlflow_client import MLflowClient
from app.integrations.snowflake_client import SnowflakeClient
from app.ml.features import split_features_target
from app.ml.metrics import evaluate_classification
from app.ml.registry import register_model as register_model_entry
from app.ml.registry import register_training_run, update_training_run


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_version() -> str:
    return datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M%S")


def train_model(dataset_uri: str, algorithm: str = "RandomForestClassifier", register_model: bool = True):
    settings = get_settings()
    run_id = str(uuid.uuid4())
    model_id = str(uuid.uuid4())
    model_name = "asset_failure_classifier"
    model_version = _utc_version()
    started_at = _utc_now_iso()

    run_payload = {
        "run_id": run_id,
        "status": "running",
        "dataset_uri": dataset_uri,
        "parameters": {"n_estimators": 120, "max_depth": 8, "random_state": 42},
        "started_at": started_at,
        "finished_at": None,
        "metrics": {},
        "model_id": model_id,
        "mlflow_run_id": None,
        "error_message": None,
    }
    register_training_run(run_payload)

    try:
        snowflake_client = SnowflakeClient()
        df = snowflake_client.load_sensor_data(dataset_uri)
        X, y = split_features_target(df)

        model = RandomForestClassifier(n_estimators=120, max_depth=8, random_state=42)
        model.fit(X, y)
        predicted = model.predict(X)
        metrics = evaluate_classification(y, predicted)

        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact_uri = artifacts_dir / f"{model_name}_{model_version}.pkl"
        joblib.dump(model, artifact_uri)
        published_artifact_uri = str(artifact_uri)
        if settings.model_artifact_backend == "blob" and is_blob_configured():
            published_artifact_uri = upload_file(
                settings.blob_models_container,
                f"{model_name}/{model_version}/model.pkl",
                artifact_uri,
            )

        mlflow_run_id = MLflowClient().log_training_run(
            run_name=f"{model_name}_{model_version}",
            parameters=run_payload["parameters"],
            metrics=metrics,
            artifact_uri=str(artifact_uri),
            tags={
                "model_name": model_name,
                "model_version": model_version,
                "algorithm": algorithm,
                "published_artifact_uri": published_artifact_uri,
            },
        )

        if register_model:
            metadata = {
                "model_id": model_id,
                "name": model_name,
                "version": model_version,
                "stage": "production",
                "algorithm": algorithm,
                "artifact_uri": published_artifact_uri,
                "metrics": metrics,
                "created_at": _utc_now_iso(),
                "promoted_at": _utc_now_iso(),
            }
            register_model_entry(metadata)

        update_training_run(
            run_id,
            {
                "status": "completed",
                "finished_at": _utc_now_iso(),
                "metrics": metrics,
                "mlflow_run_id": mlflow_run_id,
            },
        )

        return {
            "run_id": run_id,
            "status": "completed",
            "metrics": metrics,
            "model": {
                "model_id": model_id,
                "name": model_name,
                "version": model_version,
                "artifact_uri": published_artifact_uri,
                "algorithm": algorithm,
                "registered": register_model,
            },
        }
    except Exception as exc:
        update_training_run(run_id, {"status": "failed", "finished_at": _utc_now_iso(), "error_message": str(exc)})
        raise
