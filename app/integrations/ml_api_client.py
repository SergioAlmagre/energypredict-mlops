from __future__ import annotations

from typing import Any

import httpx


class MLApiClientError(Exception):
    """Raised when ML API integration fails."""


class MLApiClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"

        if self._client is not None:
            response = self._client.request(method, url, json=payload, headers=self._headers())
        else:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.request(method, url, json=payload, headers=self._headers())

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise MLApiClientError(f"ML API request failed ({response.status_code}) at {path}: {detail}")

        if not response.content:
            return {}
        return response.json()

    def predict_failure_risk(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/predict", payload)

    def train_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/models/train", payload)

    def get_current_model(self) -> dict[str, Any]:
        return self._request("GET", "/models/current")

    def list_runs(self) -> dict[str, Any]:
        return self._request("GET", "/models/runs")

    def promote_model(self, model_id: str) -> dict[str, Any]:
        return self._request("POST", f"/models/{model_id}/promote", {})
