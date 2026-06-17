from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from app.core.config import get_settings


class MLflowClient:
    """MLflow wrapper with real tracking support and local fallback for development."""

    def __init__(self, tracking_uri: str | None = None):
        settings = get_settings()
        self.tracking_uri = tracking_uri or settings.mlflow_tracking_uri
        self.registry_uri = settings.mlflow_registry_uri
        self.experiment_name = settings.mlflow_experiment_name
        self.register_model = settings.mlflow_register_model
        self.sync_production_alias = settings.mlflow_sync_production_alias
        self.production_alias = settings.mlflow_production_alias
        self.last_registered_model_version: str | None = None
        self.registered_model_name = self._resolve_registered_model_name(
            configured_name=settings.mlflow_registered_model_name,
            catalog=settings.mlflow_uc_catalog,
            schema=settings.mlflow_uc_schema,
            model_name=settings.mlflow_model_name,
        )
        self.local_runs_path = Path("artifacts") / "mlflow_runs.json"
        if settings.databricks_host and "DATABRICKS_HOST" not in os.environ:
            os.environ["DATABRICKS_HOST"] = settings.databricks_host
        if settings.databricks_token and "DATABRICKS_TOKEN" not in os.environ:
            os.environ["DATABRICKS_TOKEN"] = settings.databricks_token

    @staticmethod
    def _resolve_registered_model_name(
        configured_name: str | None,
        catalog: str | None,
        schema: str | None,
        model_name: str,
    ) -> str | None:
        if configured_name:
            return configured_name
        if catalog and schema:
            return f"{catalog}.{schema}.{model_name}"
        return None

    def log_training_run(
        self,
        run_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        artifact_uri: str,
        tags: Dict[str, str] | None = None,
        model: Any | None = None,
        input_example: Any | None = None,
    ) -> str:
        if not self.tracking_uri.startswith("local://"):
            return self._log_real_run(run_name, parameters, metrics, artifact_uri, tags, model, input_example)

        run_id = str(uuid4())
        payload = {
            "run_id": run_id,
            "run_name": run_name,
            "parameters": parameters,
            "metrics": metrics,
            "artifact_uri": artifact_uri,
            "tags": tags or {},
            "registered_model_name": self.registered_model_name if self.register_model else None,
            "registered_model_version": self.last_registered_model_version,
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "tracking_uri": self.tracking_uri,
        }

        runs = self.list_runs()
        runs.append(payload)
        self.local_runs_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_runs_path.write_text(__import__("json").dumps(runs, indent=2), encoding="utf-8")
        return run_id

    def list_runs(self) -> List[Dict[str, Any]]:
        if not self.local_runs_path.exists():
            return []
        try:
            return __import__("json").loads(self.local_runs_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _log_real_run(
        self,
        run_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        artifact_uri: str,
        tags: Dict[str, str] | None = None,
        model: Any | None = None,
        input_example: Any | None = None,
    ) -> str:
        import mlflow

        mlflow.set_tracking_uri(self.tracking_uri)
        if self.registry_uri:
            mlflow.set_registry_uri(self.registry_uri)
        mlflow.set_experiment(self.experiment_name)
        with mlflow.start_run(run_name=run_name) as run:
            mlflow.log_params(parameters)
            mlflow.log_metrics(metrics)
            mlflow.set_tags(tags or {})
            mlflow.set_tag("artifact_uri", artifact_uri)
            if self.register_model:
                if model is None:
                    raise ValueError("MLFLOW_REGISTER_MODEL=true requires a trained model object.")
                if not self.registered_model_name:
                    raise ValueError(
                        "MLFLOW_REGISTER_MODEL=true requires MLFLOW_REGISTERED_MODEL_NAME "
                        "or MLFLOW_UC_CATALOG plus MLFLOW_UC_SCHEMA."
                    )
                import mlflow.sklearn as mlflow_sklearn

                mlflow.set_tag("registered_model_name", self.registered_model_name)
                mlflow.set_tag("registry_uri", self.registry_uri or "")
                mlflow_sklearn.log_model(
                    sk_model=model,
                    artifact_path="model",
                    input_example=input_example,
                    registered_model_name=self.registered_model_name,
                )
                self.last_registered_model_version = self._find_model_version_for_run(run.info.run_id)
                if self.last_registered_model_version:
                    mlflow.set_tag("registered_model_version", self.last_registered_model_version)
            path = Path(artifact_uri)
            if path.exists():
                mlflow.log_artifact(str(path))
            return run.info.run_id

    def _find_model_version_for_run(self, run_id: str) -> str | None:
        if not self.registered_model_name:
            return None
        try:
            import mlflow
            from mlflow.tracking import MlflowClient as TrackingClient

            mlflow.set_tracking_uri(self.tracking_uri)
            if self.registry_uri:
                mlflow.set_registry_uri(self.registry_uri)
            versions = TrackingClient().search_model_versions(f"run_id = '{run_id}'")
            for version in versions:
                if version.name == self.registered_model_name:
                    return str(version.version)
        except Exception:
            return None
        return None

    def set_production_alias(
        self,
        registered_model_name: str | None = None,
        registered_model_version: str | None = None,
    ) -> Dict[str, Any]:
        model_name = registered_model_name or self.registered_model_name
        model_version = registered_model_version or self.last_registered_model_version
        if not self.sync_production_alias:
            return {"status": "skipped", "reason": "MLFLOW_SYNC_PRODUCTION_ALIAS is disabled."}
        if not model_name or not model_version:
            return {"status": "skipped", "reason": "Missing registered model name or version."}
        if self.tracking_uri.startswith("local://"):
            return {"status": "skipped", "reason": "Local MLflow mode does not support registry aliases."}

        try:
            import mlflow
            from mlflow.tracking import MlflowClient as TrackingClient

            mlflow.set_tracking_uri(self.tracking_uri)
            if self.registry_uri:
                mlflow.set_registry_uri(self.registry_uri)
            TrackingClient().set_registered_model_alias(
                name=model_name,
                alias=self.production_alias,
                version=str(model_version),
            )
            return {
                "status": "synced",
                "alias": self.production_alias,
                "registered_model_name": model_name,
                "registered_model_version": str(model_version),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "alias": self.production_alias,
                "registered_model_name": model_name,
                "registered_model_version": str(model_version),
                "error": str(exc),
            }
