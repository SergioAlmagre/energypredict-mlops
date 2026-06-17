import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.blob_storage import BlobStorageUnavailable
from app.ml.registry import get_current_model_metadata

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/live",
    summary="Liveness probe",
    description="Returns HTTP 200 when the FastAPI process is alive.",
    responses={200: {"description": "API process is alive."}},
)
def live():
    return {"status": "ok", "service": "energypredict-api"}


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns HTTP 200 only when the API can receive traffic: DB is reachable and model metadata is available.",
    responses={
        200: {"description": "API is ready to receive traffic."},
        503: {"description": "API is alive but not ready; response detail includes an operational reason code."},
    },
)
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "unavailable",
                "model": "not_checked",
                "reason": "database_unreachable",
            },
        ) from exc

    try:
        model = get_current_model_metadata()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "ok",
                "model": "unavailable",
                "reason": "no_production_model_registered",
            },
        ) from exc
    except BlobStorageUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "ok",
                "model": "unavailable",
                "reason": "registry_backend_unreachable",
            },
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "ok",
                "model": "unavailable",
                "reason": "registry_payload_invalid",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "ok",
                "model": "unavailable",
                "reason": "model_readiness_check_failed",
            },
        ) from exc
    return {
        "status": "ready",
        "database": "ok",
        "model": "ok",
        "model_name": model.get("name"),
        "model_version": model.get("version"),
    }
