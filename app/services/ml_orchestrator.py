from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.integrations.ml_api_client import MLApiClient
from app.ml.predict import predict_failure_risk
from app.ml.service import get_current_model, list_training_runs, promote_model_to_production, train_model_service


@dataclass
class TrainAndPromoteResult:
    run_id: str
    model_id: str
    promoted: bool
    promotion_reason: str
    metrics: dict[str, float]


class MLOrchestrator:
    def __init__(self, client: MLApiClient | None = None, use_local_services: bool = False) -> None:
        settings = get_settings()
        self.min_f1_score = settings.auto_promote_min_f1_score
        self.client = client or MLApiClient(base_url=settings.ml_api_base_url)
        self.use_local_services = use_local_services

    def train_and_optionally_promote(self, payload: dict[str, Any]) -> TrainAndPromoteResult:
        train_result = train_model_service(payload) if self.use_local_services else self.client.train_model(payload)
        metrics = train_result.get("metrics", {})
        model = train_result.get("model", {})
        run_id = train_result.get("run_id", "")
        model_id = model.get("model_id", "")

        f1_score = float(metrics.get("f1_score", 0.0))
        if not model_id:
            return TrainAndPromoteResult(
                run_id=run_id,
                model_id="",
                promoted=False,
                promotion_reason="No model_id returned by training endpoint.",
                metrics=metrics,
            )

        if f1_score >= self.min_f1_score:
            if self.use_local_services:
                promote_model_to_production(model_id)
            else:
                self.client.promote_model(model_id)
            return TrainAndPromoteResult(
                run_id=run_id,
                model_id=model_id,
                promoted=True,
                promotion_reason=f"Auto-promoted: f1_score={f1_score:.4f} >= threshold={self.min_f1_score:.4f}",
                metrics=metrics,
            )

        return TrainAndPromoteResult(
            run_id=run_id,
            model_id=model_id,
            promoted=False,
            promotion_reason=f"Not promoted: f1_score={f1_score:.4f} < threshold={self.min_f1_score:.4f}",
            metrics=metrics,
        )

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        return predict_failure_risk(payload) if self.use_local_services else self.client.predict_failure_risk(payload)

    def current_model(self) -> dict[str, Any]:
        return get_current_model() if self.use_local_services else self.client.get_current_model()

    def list_runs(self) -> dict[str, Any]:
        return {"items": list_training_runs()} if self.use_local_services else self.client.list_runs()
