from app.ml.train import train_model


def test_model_can_train_and_log_metrics():
    result = train_model(dataset_uri="data/synthetic_sensor_data.csv")

    assert result["status"] == "completed"
    metrics = result["metrics"]

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics

    for metric in ("accuracy", "precision", "recall", "f1_score"):
        assert 0.0 <= metrics[metric] <= 1.0

    assert result["model"]["artifact_uri"].endswith(".pkl")
