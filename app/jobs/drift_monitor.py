from __future__ import annotations

import json
import os
import sys

from app.db.session import SessionLocal
from app.ml.drift import evaluate_data_drift


def main() -> int:
    trigger_retraining = os.getenv("DRIFT_TRIGGER_RETRAINING", "false").lower() == "true"
    window_hours_value = os.getenv("DRIFT_MONITOR_WINDOW_HOURS")
    window_hours = int(window_hours_value) if window_hours_value else None

    with SessionLocal() as db:
        report = evaluate_data_drift(
            db=db,
            window_hours=window_hours,
            trigger_retraining=trigger_retraining,
        )

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
