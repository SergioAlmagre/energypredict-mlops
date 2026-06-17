import json
import logging
import time
import uuid

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from jose import JWTError, jwt

from app.api.routes_auth import router as auth_router
from app.api.routes_admin import router as admin_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_health import router as health_router
from app.api.routes_models import router as models_router
from app.api.routes_predictions import router as predictions_router
from app.api.routes_stream import router as stream_router
from app.core.config import get_settings
from app.core.metrics import metrics_response, observe_http_request, should_skip_http_metrics
from app.db.session import Base, SessionLocal, engine
from app.services.risk_policy_service import get_or_create_active_policy
from app.services.streaming_service import get_or_create_simulation_state
from app.workers.simulation_worker import simulation_worker

settings = get_settings()
Base.metadata.create_all(bind=engine)
try:
    with SessionLocal() as bootstrap_db:
        get_or_create_active_policy(bootstrap_db)
        get_or_create_simulation_state(bootstrap_db)
except Exception:
    # Runtime policies are lazily created during API calls if bootstrap fails.
    pass
logger = logging.getLogger("energypredict.request")

openapi_tags = [
    {"name": "health", "description": "Runtime health checks used by Kubernetes probes and operators."},
    {"name": "auth", "description": "JWT authentication and current-user endpoints."},
    {"name": "predictions", "description": "Online inference endpoints for industrial asset risk scoring."},
    {"name": "models", "description": "Training, model registry, promotion and MLOps integration endpoints."},
    {"name": "admin", "description": "Administrative controls for simulation and risk thresholds."},
    {"name": "stream", "description": "Latest sensor events produced by streaming ingestion."},
    {"name": "alerts", "description": "Active predictive-maintenance alerts."},
]

app = FastAPI(
    title=settings.app_name,
    description=(
        "Industrial predictive-maintenance MLOps API. The service exposes JWT-protected inference, "
        "model training orchestration, AKS health probes and operational endpoints."
    ),
    version="1.0.0",
    contact={"name": "EnergyPredict MLOps"},
    openapi_tags=openapi_tags,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(predictions_router, prefix=settings.api_v1_prefix)
app.include_router(models_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(stream_router, prefix=settings.api_v1_prefix)
app.include_router(alerts_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup_background_workers():
    if settings.api_simulation_worker_enabled:
        simulation_worker.start()


@app.on_event("shutdown")
def shutdown_background_workers():
    simulation_worker.stop()


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.environment == "prod":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def _identity_from_jwt(request: Request) -> tuple[str, str]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return "anonymous", "anonymous"

    token = auth_header[7:].strip()
    if not token:
        return "anonymous", "anonymous"

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
        )
        user = payload.get("email", "unknown")
        role = payload.get("role", "unknown")
        return str(user), str(role)
    except JWTError:
        return "invalid_token", "unknown"


@app.middleware("http")
async def request_trace_logging_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    trace_id = request.headers.get("X-Trace-Id") or request.headers.get("X-Request-Id") or str(uuid.uuid4())
    user, role = _identity_from_jwt(request)
    status_code = 500

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    finally:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route = request.url.path
        route_obj = request.scope.get("route")
        if route_obj and getattr(route_obj, "path", None):
            route = route_obj.path

        logger.info(
            json.dumps(
                {
                    "trace_id": trace_id,
                    "method": request.method,
                    "route": route,
                    "status": status_code,
                    "latency_ms": elapsed_ms,
                    "user": user,
                    "role": role,
                }
            )
        )
        if not should_skip_http_metrics(request.url.path):
            observe_http_request(request.method, route, status_code, started_at)

    response.headers["X-Trace-Id"] = trace_id
    return response


@app.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_response()
