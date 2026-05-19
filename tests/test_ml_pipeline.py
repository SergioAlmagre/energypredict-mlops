from app.ml.predict import risk_level_from_probability
from app.ml.service import get_current_model, list_training_runs, promote_model_to_production, train_model_service


def test_risk_level_thresholds():
    assert risk_level_from_probability(0.2) == "low"
    assert risk_level_from_probability(0.5) == "medium"
    assert risk_level_from_probability(0.8) == "high"


def test_train_and_promote_pipeline():
    result = train_model_service({"dataset_uri": "data/synthetic_sensor_data.csv", "register_model": True})
    assert result["status"] == "completed"
    assert "model" in result
    model_id = result["model"].get("model_id") or result["run_id"]

    promoted = promote_model_to_production(model_id)
    assert promoted["stage"] == "production"

    current = get_current_model()
    assert current["stage"] == "production"
    assert current["version"]

    runs = list_training_runs()
    assert len(runs) >= 1
