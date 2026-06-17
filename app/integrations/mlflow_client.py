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
        self.local_runs_path = Path("artifacts") / "mlflow_runs.json"
        if settings.databricks_host and "DATABRICKS_HOST" not in os.environ:
            os.environ["DATABRICKS_HOST"] = settings.databricks_host
        if settings.databricks_token and "DATABRICKS_TOKEN" not in os.environ:
            os.environ["DATABRICKS_TOKEN"] = settings.databricks_token

    def log_training_run(
        self,
        run_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        artifact_uri: str,
        tags: Dict[str, str] | None = None,
    ) -> str:
        if not self.tracking_uri.startswith("local://"):
            return self._log_real_run(run_name, parameters, metrics, artifact_uri, tags)

        run_id = str(uuid4())
        payload = {
            "run_id": run_id,
            "run_name": run_name,
            "parameters": parameters,
            "metrics": metrics,
            "artifact_uri": artifact_uri,
            "tags": tags or {},
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
            path = Path(artifact_uri)
            if path.exists():
                mlflow.log_artifact(str(path))
            return run.info.run_id
