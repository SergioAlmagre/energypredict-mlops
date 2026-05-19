from app.core.config import get_settings
from app.services.ml_orchestrator import MLOrchestrator


class FakeClient:
    def __init__(self, f1_score: float):
        self.f1_score = f1_score
        self.promoted_model_ids: list[str] = []

    def train_model(self, _payload):
        return {
            "run_id": "run-1",
            "model": {"model_id": "model-1"},
            "metrics": {"accuracy": 0.9, "precision": 0.9, "recall": 0.8, "f1_score": self.f1_score},
        }

    def promote_model(self, model_id: str):
        self.promoted_model_ids.append(model_id)
        return {"model_id": model_id, "stage": "production"}

    def predict_failure_risk(self, payload):
        return {"risk_level": "high", "failure_probability": 0.91, "echo": payload}

    def get_current_model(self):
        return {"name": "asset_failure_classifier", "version": "1.2.3", "stage": "production"}

    def list_runs(self):
        return {"items": [{"run_id": "run-1", "status": "completed"}]}


def test_orchestrator_auto_promotes_when_f1_meets_threshold(monkeypatch):
    monkeypatch.setenv("AUTO_PROMOTE_MIN_F1_SCORE", "0.80")
    get_settings.cache_clear()
    orchestrator = MLOrchestrator(client=FakeClient(f1_score=0.85))

    result = orchestrator.train_and_optionally_promote({"dataset_uri": "data/synthetic_sensor_data.csv"})

    assert result.promoted is True
    assert result.model_id == "model-1"


def test_orchestrator_skips_promotion_when_f1_is_low(monkeypatch):
    monkeypatch.setenv("AUTO_PROMOTE_MIN_F1_SCORE", "0.95")
    get_settings.cache_clear()
    orchestrator = MLOrchestrator(client=FakeClient(f1_score=0.85))

    result = orchestrator.train_and_optionally_promote({"dataset_uri": "data/synthetic_sensor_data.csv"})

    assert result.promoted is False
    assert "Not promoted" in result.promotion_reason


def test_orchestrator_passthrough_calls(monkeypatch):
    monkeypatch.setenv("AUTO_PROMOTE_MIN_F1_SCORE", "0.80")
    get_settings.cache_clear()
    orchestrator = MLOrchestrator(client=FakeClient(f1_score=0.85))

    pred = orchestrator.predict({"asset_code": "PUMP-001"})
    current = orchestrator.current_model()
    runs = orchestrator.list_runs()

    assert pred["risk_level"] == "high"
    assert current["stage"] == "production"
    assert len(runs["items"]) == 1
