from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

HTTP_REQUESTS_TOTAL = Counter(
    "energypredict_http_requests_total",
    "Total HTTP requests by method, route and status code.",
    ["method", "route", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "energypredict_http_request_duration_seconds",
    "HTTP request latency in seconds by method and route.",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
PREDICTIONS_TOTAL = Counter(
    "energypredict_predictions_total",
    "Total predictions by source, risk level and model version.",
    ["source", "risk_level", "model_version"],
)
ACTIVE_ALERTS_GAUGE = Gauge(
    "energypredict_active_alerts",
    "Current active predictive-maintenance alerts by severity.",
    ["severity"],
)
DRIFT_REPORTS_TOTAL = Counter(
    "energypredict_drift_reports_total",
    "Total drift reports by status and model version.",
    ["status", "model_version"],
)
DRIFT_MAX_FEATURE_PSI = Gauge(
    "energypredict_drift_max_feature_psi",
    "Latest maximum feature PSI by model version.",
    ["model_version"],
)
DRIFT_GLOBAL_PSI = Gauge(
    "energypredict_drift_global_psi",
    "Latest average/global PSI by model version.",
    ["model_version"],
)
TRAINING_JOBS_TRIGGERED_TOTAL = Counter(
    "energypredict_training_jobs_triggered_total",
    "Total training jobs triggered by source.",
    ["source"],
)


def should_skip_http_metrics(path: str) -> bool:
    return path == "/metrics" or path.endswith("/health/live") or path.endswith("/health/ready")


def observe_http_request(method: str, route: str, status_code: int, started_at: float) -> None:
    elapsed = time.perf_counter() - started_at
    HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status_code=str(status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, route=route).observe(elapsed)


def observe_prediction(source: str, risk_level: str, model_version: str | None) -> None:
    PREDICTIONS_TOTAL.labels(
        source=source,
        risk_level=risk_level,
        model_version=model_version or "unknown",
    ).inc()


def observe_active_alerts(counts_by_severity: dict[str, int]) -> None:
    for severity in ("medium", "high"):
        ACTIVE_ALERTS_GAUGE.labels(severity=severity).set(counts_by_severity.get(severity, 0))


def observe_drift_report(report: dict) -> None:
    model_version = str(report.get("model_version") or "unknown")
    status = str(report.get("status") or "unknown")
    DRIFT_REPORTS_TOTAL.labels(status=status, model_version=model_version).inc()
    if report.get("max_feature_psi") is not None:
        DRIFT_MAX_FEATURE_PSI.labels(model_version=model_version).set(float(report["max_feature_psi"]))
    if report.get("global_psi") is not None:
        DRIFT_GLOBAL_PSI.labels(model_version=model_version).set(float(report["global_psi"]))
    if report.get("retraining_triggered"):
        TRAINING_JOBS_TRIGGERED_TOTAL.labels(source="data_drift").inc()


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
