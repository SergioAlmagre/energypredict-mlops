# Runtime artifacts

This directory is intentionally kept out of Git except for this note.

Local training and tests may create MLflow fallback logs and temporary model artifacts here. In cloud, model artifacts are published to Azure Blob Storage and training metadata is logged to Databricks MLflow.
