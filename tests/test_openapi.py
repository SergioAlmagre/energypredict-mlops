from app.main import app


def test_openapi_schema_exposes_core_metadata_and_paths():
    schema = app.openapi()

    assert schema["info"]["title"] == "EnergyPredict MLOps API"
    assert schema["info"]["version"] == "1.0.0"
    assert "/api/v1/predict" in schema["paths"]
    assert "/api/v1/models/train" in schema["paths"]
    assert "/api/v1/health/ready" in schema["paths"]

    tag_names = {tag["name"] for tag in schema["tags"]}
    assert {"health", "predictions", "models"}.issubset(tag_names)
