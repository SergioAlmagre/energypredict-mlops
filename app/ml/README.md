# ML/MLOps Module

This module provides an MVP ML lifecycle designed to avoid blocking backend development.

## Backend-consumable API

- `app.ml.predict.predict_failure_risk(payload)`
- `app.ml.service.train_model_service(payload)`
- `app.ml.service.get_current_model()`
- `app.ml.service.list_training_runs()`
- `app.ml.service.promote_model_to_production(model_id)`

## What is local vs production-ready abstraction

- Local training and inference are fully functional.
- MLflow is wrapped by `app/integrations/mlflow_client.py` (local JSON tracking in MVP).
- Databricks is abstracted in `app/integrations/databricks_client.py` via `trigger_training_job(...)` stub.
- Snowflake is abstracted in `app/integrations/snowflake_client.py` via `load_sensor_data(...)` currently backed by CSV.

## Artifacts and registry

- Model artifacts are saved in `artifacts/*.pkl`.
- Lightweight model registry and training runs are tracked in `models/registry.json`.
- MLflow-like run logs are tracked in `artifacts/mlflow_runs.json`.
