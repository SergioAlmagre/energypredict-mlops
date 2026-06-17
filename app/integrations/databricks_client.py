from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import requests

from app.core.config import get_settings


class DatabricksClient:
    """Training launcher for K8s Jobs, Databricks Jobs API, or local stub fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self.workspace_url = settings.databricks_workspace_url
        self.token = settings.databricks_token
        self.job_id = settings.databricks_job_id
        self.training_mode = settings.training_mode
        self.k8s_namespace = settings.k8s_namespace
        self.k8s_training_job_image = settings.k8s_training_job_image
        self.k8s_training_job_service_account = settings.k8s_training_job_service_account
        self.k8s_config_map_name = settings.k8s_config_map_name
        self.k8s_secret_name = settings.k8s_secret_name

    def is_configured(self) -> bool:
        return bool(self.workspace_url and self.token and self.job_id)

    def health_check(self) -> Dict[str, Any]:
        if self.training_mode == "k8s_job":
            return {
                "mode": "k8s_job",
                "configured": bool(self.k8s_training_job_image),
                "status": "ok" if self.k8s_training_job_image else "missing_image",
                "namespace": self.k8s_namespace,
            }

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
        if self.training_mode == "k8s_job":
            return self._create_k8s_training_job(dataset_uri, parameters, experiment_name)

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

    def _create_k8s_training_job(
        self,
        dataset_uri: str,
        parameters: Dict[str, Any],
        experiment_name: str,
    ) -> Dict[str, Any]:
        run_id = str(uuid4())
        if not self.k8s_training_job_image:
            return {
                "job_run_id": run_id,
                "status": "submitted",
                "mode": "k8s_job_stub",
                "experiment_name": experiment_name,
                "dataset_uri": dataset_uri,
                "parameters": parameters,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "note": "K8S_TRAINING_JOB_IMAGE is not configured; no Kubernetes Job was created.",
            }

        try:
            from kubernetes import client, config
        except Exception:
            return {
                "job_run_id": run_id,
                "status": "submitted",
                "mode": "k8s_job_stub",
                "experiment_name": experiment_name,
                "dataset_uri": dataset_uri,
                "parameters": parameters,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "note": "kubernetes package is not available; no Kubernetes Job was created.",
            }

        try:
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()

            job_name = f"energypredict-training-{run_id[:8]}"
            env = [
                client.V1EnvVar(name="DATASET_URI", value=dataset_uri),
                client.V1EnvVar(name="EXPERIMENT_NAME", value=experiment_name),
                client.V1EnvVar(name="REGISTER_MODEL", value=str(parameters.get("register_model", True)).lower()),
            ]
            env.extend(client.V1EnvVar(name=f"TRAIN_PARAM_{key.upper()}", value=str(value)) for key, value in parameters.items())
            container = client.V1Container(
                name="training",
                image=self.k8s_training_job_image,
                image_pull_policy="Always",
                env=env,
                env_from=[
                    client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name=self.k8s_config_map_name)),
                    client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=self.k8s_secret_name)),
                ],
            )
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": "energypredict-training"}),
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    service_account_name=self.k8s_training_job_service_account,
                    containers=[container],
                ),
            )
            job = client.V1Job(
                metadata=client.V1ObjectMeta(name=job_name),
                spec=client.V1JobSpec(
                    backoff_limit=1,
                    ttl_seconds_after_finished=86400,
                    template=template,
                ),
            )
            client.BatchV1Api().create_namespaced_job(namespace=self.k8s_namespace, body=job)
            mode = "k8s_job"
            note = None
        except Exception as exc:
            mode = "k8s_job_stub"
            note = f"Kubernetes Job creation failed: {exc}"
            job_name = f"energypredict-training-{run_id[:8]}"

        result = {
            "job_run_id": run_id,
            "k8s_job_name": job_name,
            "status": "submitted",
            "mode": mode,
            "experiment_name": experiment_name,
            "dataset_uri": dataset_uri,
            "parameters": parameters,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        if note:
            result["note"] = note
        return result
