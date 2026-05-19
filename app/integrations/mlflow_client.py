from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4


class MLflowClient:
    """Small wrapper that logs runs locally and supports future real MLflow integration."""

    def __init__(self, tracking_uri: str | None = None):
        self.tracking_uri = tracking_uri or "local://artifacts/mlflow"
        self.local_runs_path = Path("artifacts") / "mlflow_runs.json"

    def log_training_run(
        self,
        run_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        artifact_uri: str,
        tags: Dict[str, str] | None = None,
    ) -> str:
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
