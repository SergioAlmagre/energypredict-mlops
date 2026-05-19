from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import requests

from app.core.config import get_settings


class DatabricksClient:
    """Hybrid Databricks client: real Jobs API when configured, stub fallback otherwise."""

    def __init__(self) -> None:
        settings = get_settings()
        self.workspace_url = settings.databricks_workspace_url
        self.token = settings.databricks_token
        self.job_id = settings.databricks_job_id

    def is_configured(self) -> bool:
        return bool(self.workspace_url and self.token and self.job_id)

    def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "mode": "stub",
                "configured": False,
                "status": "not_configured",
                "message": "Set DATABRICKS_WORKSPACE_URL, DATABRICKS_TOKEN and DATABRICKS_JOB_ID for real mode.",
            }

        url = f"{self.workspace_url.rstrip('/')}/api/2.1/jobs/get"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers, params={"job_id": self.job_id}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        return {
            "mode": "real",
            "configured": True,
            "status": "ok",
            "job_id": self.job_id,
            "job_name": payload.get("settings", {}).get("name"),
        }

    def trigger_training_job(
        self,
        dataset_uri: str,
        parameters: Dict[str, Any],
        experiment_name: str = "energypredict-training",
    ) -> Dict[str, Any]:
        if self.is_configured():
            url = f"{self.workspace_url.rstrip('/')}/api/2.1/jobs/run-now"
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "job_id": int(self.job_id),
                "notebook_params": {
                    "dataset_uri": dataset_uri,
                    "experiment_name": experiment_name,
                    **{k: str(v) for k, v in parameters.items()},
                },
            }
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return {
                "job_run_id": f"dbx-{data.get('run_id')}",
                "status": "submitted",
                "mode": "real",
                "experiment_name": experiment_name,
                "dataset_uri": dataset_uri,
                "parameters": parameters,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            }

        return {
            "job_run_id": f"dbx-{uuid4()}",
            "status": "submitted",
            "mode": "stub",
            "experiment_name": experiment_name,
            "dataset_uri": dataset_uri,
            "parameters": parameters,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "note": "Stub fallback because Databricks credentials are not configured.",
        }
