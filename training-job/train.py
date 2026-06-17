from __future__ import annotations

import os
import sys

import requests

from app.ml.train import train_model


def main() -> int:
    dataset_uri = os.getenv("DATASET_URI", "data/synthetic_sensor_data.csv")
    algorithm = os.getenv("ALGORITHM", "RandomForestClassifier")
    register_model = os.getenv("REGISTER_MODEL", "true").lower() == "true"
    api_base = os.getenv("API_INTERNAL_BASE_URL")
    reload_token = os.getenv("MODEL_RELOAD_TOKEN")

    result = train_model(dataset_uri=dataset_uri, algorithm=algorithm, register_model=register_model)

    if api_base and reload_token:
        headers = {"Authorization": f"Bearer {reload_token}"}
        try:
            requests.post(f"{api_base.rstrip('/')}/models/reload", json=result.get("model", {}), headers=headers, timeout=15)
        except Exception:
            pass

    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
