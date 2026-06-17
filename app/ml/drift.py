from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import pandas as pd
import requests
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import observe_drift_report
from app.db.models import Prediction, SensorEvent
from app.integrations.databricks_client import DatabricksClient
from app.ml.registry import get_current_model_metadata, register_drift_report

FEATURE_COLUMNS = [
    "temperature",
    "pressure",
    "vibration",
    "flow_rate",
    "energy_consumption",
    "operating_hours",
]

EPSILON = 1e-6


def build_feature_baseline(features: pd.DataFrame, bins: int = 10) -> dict[str, Any]:
    baseline: dict[str, Any] = {"type": "histogram", "created_at": datetime.now(timezone.utc).isoformat(), "features": {}}
    for column in FEATURE_COLUMNS:
        if column not in features.columns:
            continue
        series = pd.to_numeric(features[column], errors="coerce").dropna()
        if series.empty:
            continue
        edges = _quantile_edges(series, bins=bins)
        proportions = _histogram_proportions(series, edges)
        baseline["features"][column] = {
            "count": int(series.count()),
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "min": float(series.min()),
            "max": float(series.max()),
            "bin_edges": [float(value) for value in edges],
            "bin_proportions": proportions,
        }
    return baseline


def evaluate_data_drift(
    db: Session,
    window_hours: int | None = None,
    trigger_retraining: bool | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    window = window_hours or settings.drift_monitor_window_hours
    should_trigger_retraining = settings.drift_retraining_enabled if trigger_retraining is None else trigger_retraining

    model = get_current_model_metadata()
    baseline = model.get("feature_baseline") or {}
    feature_baselines = baseline.get("features", {})
    since = datetime.now(timezone.utc) - timedelta(hours=window)
    production_features = _load_recent_feature_frame(db, since=since)

    report = {
        "report_id": str(uuid4()),
        "model_id": model.get("model_id"),
        "model_name": model.get("name"),
        "model_version": model.get("version"),
        "window_hours": window,
        "sample_count": int(len(production_features)),
        "min_samples": settings.drift_monitor_min_samples,
        "warning_threshold": settings.drift_psi_warning_threshold,
        "retrain_threshold": settings.drift_psi_retrain_threshold,
        "status": "insufficient_data",
        "global_psi": None,
        "max_feature_psi": None,
        "features": {},
        "retraining_triggered": False,
        "training_job": None,
        "alert": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if not feature_baselines:
        report["status"] = "missing_baseline"
        _attach_alert_result(report, settings)
        return register_drift_report(report)

    if len(production_features) < settings.drift_monitor_min_samples:
        _attach_alert_result(report, settings)
        return register_drift_report(report)

    feature_scores = {}
    for column, feature_baseline in feature_baselines.items():
        if column not in production_features.columns:
            continue
        actual = pd.to_numeric(production_features[column], errors="coerce").dropna()
        if actual.empty:
            continue
        expected_proportions = feature_baseline.get("bin_proportions", [])
        edges = feature_baseline.get("bin_edges", [])
        if len(edges) < 2 or not expected_proportions:
            continue
        actual_proportions = _histogram_proportions(actual, edges)
        psi = _population_stability_index(expected_proportions, actual_proportions)
        feature_scores[column] = {
            "psi": psi,
            "sample_count": int(actual.count()),
            "baseline_mean": feature_baseline.get("mean"),
            "actual_mean": float(actual.mean()),
        }

    if not feature_scores:
        report["status"] = "missing_features"
        _attach_alert_result(report, settings)
        return register_drift_report(report)

    scores = [item["psi"] for item in feature_scores.values()]
    global_psi = float(sum(scores) / len(scores))
    max_feature_psi = float(max(scores))
    report["features"] = feature_scores
    report["global_psi"] = global_psi
    report["max_feature_psi"] = max_feature_psi

    if max_feature_psi >= settings.drift_psi_retrain_threshold:
        report["status"] = "retrain_required"
    elif max_feature_psi >= settings.drift_psi_warning_threshold:
        report["status"] = "warning"
    else:
        report["status"] = "ok"

    if should_trigger_retraining and report["status"] == "retrain_required":
        report["training_job"] = DatabricksClient().trigger_training_job(
            dataset_uri=settings.drift_retraining_dataset_uri,
            parameters={
                "register_model": True,
                "trigger": "data_drift",
                "source_report_id": report["report_id"],
                "max_feature_psi": round(max_feature_psi, 6),
            },
            experiment_name=settings.mlflow_experiment_name,
        )
        report["retraining_triggered"] = True

    _attach_alert_result(report, settings)
    return register_drift_report(report)


def _load_recent_feature_frame(db: Session, since: datetime) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    predictions = db.query(Prediction).filter(Prediction.created_at >= since).all()
    for prediction in predictions:
        records.append({key: prediction.input_payload.get(key) for key in FEATURE_COLUMNS})

    sensor_events = db.query(SensorEvent).filter(SensorEvent.created_at >= since).all()
    for event in sensor_events:
        records.append({key: event.telemetry_payload.get(key) for key in FEATURE_COLUMNS})

    return pd.DataFrame(records, columns=FEATURE_COLUMNS)


def _quantile_edges(series: pd.Series, bins: int) -> list[float]:
    quantiles = [index / bins for index in range(bins + 1)]
    edges = sorted({float(value) for value in series.quantile(quantiles).tolist()})
    if len(edges) < 2:
        value = float(series.iloc[0])
        return [value - 0.5, value + 0.5]
    edges[0] = min(edges[0], float(series.min())) - EPSILON
    edges[-1] = max(edges[-1], float(series.max())) + EPSILON
    return edges


def _histogram_proportions(series: pd.Series, edges: list[float]) -> list[float]:
    counts = pd.cut(series, bins=edges, include_lowest=True, duplicates="drop").value_counts(sort=False)
    total = int(counts.sum())
    if total == 0:
        return [0.0 for _ in counts]
    return [float(count / total) for count in counts]


def _population_stability_index(expected: list[float], actual: list[float]) -> float:
    length = min(len(expected), len(actual))
    psi = 0.0
    for index in range(length):
        expected_value = max(float(expected[index]), EPSILON)
        actual_value = max(float(actual[index]), EPSILON)
        psi += (actual_value - expected_value) * __import__("math").log(actual_value / expected_value)
    return float(psi)


def _attach_alert_result(report: dict[str, Any], settings: Any) -> None:
    if report.get("status") not in {"warning", "retrain_required"}:
        report["alert"] = {"status": "skipped", "reason": "Report status does not require alerting."}
        observe_drift_report(report)
        return
    if not settings.drift_alert_webhook_url:
        report["alert"] = {"status": "skipped", "reason": "DRIFT_ALERT_WEBHOOK_URL is not configured."}
        observe_drift_report(report)
        return

    payload = {
        "event_type": "energypredict.data_drift",
        "status": report.get("status"),
        "report_id": report.get("report_id"),
        "model_name": report.get("model_name"),
        "model_version": report.get("model_version"),
        "global_psi": report.get("global_psi"),
        "max_feature_psi": report.get("max_feature_psi"),
        "retraining_triggered": report.get("retraining_triggered"),
        "created_at": report.get("created_at"),
    }
    try:
        response = requests.post(settings.drift_alert_webhook_url, json=payload, timeout=10)
        report["alert"] = {"status": "sent", "http_status": response.status_code}
    except Exception as exc:
        report["alert"] = {"status": "failed", "error": str(exc)}

    observe_drift_report(report)
