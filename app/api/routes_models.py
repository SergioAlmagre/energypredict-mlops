from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.core.config import get_settings
from app.db.models import TrainingRun, User
from app.db.session import get_db
from app.integrations.databricks_client import DatabricksClient
from app.integrations.mlflow_client import MLflowClient
from app.integrations.snowflake_client import SnowflakeClient
from app.ml.drift import evaluate_data_drift
from app.ml.service import (
    get_current_model,
    list_drift_reports,
    list_training_runs,
    promote_model_to_production,
    train_model_service,
)
from app.schemas.prediction import TrainAndPromoteResponse, TrainModelRequest, TrainModelResponse
from app.services.ml_orchestrator import MLOrchestrator

router = APIRouter(prefix="/models", tags=["models"])


@router.get(
    "/current",
    summary="Get current production model",
    responses={
        200: {"description": "Current production model metadata."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Authenticated user does not have access to model metadata."},
        404: {"description": "No model has been registered yet."},
    },
)
def current_model(current_user: User = Depends(require_roles("consumer", "analyst", "ml_engineer", "admin"))):
    return get_current_model()


@router.post(
    "/train",
    response_model=TrainModelResponse | dict,
    summary="Train a model or submit a remote training job",
    description=(
        "In local mode this endpoint trains synchronously and returns model metrics. "
        "In cloud mode it submits a Kubernetes/Databricks training job and returns HTTP 202."
    ),
    responses={
        200: {"description": "Training completed synchronously in local mode."},
        202: {"description": "Training job submitted in cloud mode."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can train models."},
        422: {"description": "Invalid training request."},
    },
)
def train_model_endpoint(
    payload: TrainModelRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    settings = get_settings()
    if settings.training_mode in {"k8s_job", "databricks"}:
        result = DatabricksClient().trigger_training_job(
            dataset_uri=payload.dataset_uri,
            parameters={**payload.parameters, "register_model": payload.register_model, "algorithm": payload.algorithm},
            experiment_name=settings.mlflow_experiment_name,
        )
        db.add(
            TrainingRun(
                run_id=result["job_run_id"],
                status="submitted",
                dataset_uri=payload.dataset_uri,
                model_id=None,
                model_version=None,
                metrics={},
                parameters=payload.model_dump().get("parameters", {}),
                created_by_user_id=current_user.id,
            )
        )
        db.commit()
        response.status_code = status.HTTP_202_ACCEPTED
        return result

    payload_data = payload.model_dump()
    result = train_model_service(payload_data)
    db_run = TrainingRun(
        run_id=result["run_id"],
        status=result["status"],
        dataset_uri=payload.dataset_uri,
        model_id=result["model"]["model_id"],
        model_version=result["model"]["version"],
        metrics=result["metrics"],
        parameters=payload_data.get("parameters", {}),
        created_by_user_id=current_user.id,
    )
    db.add(db_run)
    db.commit()
    return result


@router.post(
    "/train/remote",
    summary="Submit remote training job",
    responses={
        200: {"description": "Remote training job submitted."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can train models."},
        422: {"description": "Invalid training request."},
    },
)
def train_model_remote_databricks(
    payload: TrainModelRequest,
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    client = DatabricksClient()
    result = client.trigger_training_job(
        dataset_uri=payload.dataset_uri,
        parameters=payload.parameters,
        experiment_name="energypredict-training",
    )
    return result


@router.post(
    "/reload",
    summary="Reload current model metadata",
    responses={
        200: {"description": "Current model metadata reloaded."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can reload models."},
    },
)
def reload_model(
    payload: dict | None = None,
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    current = get_current_model()
    return {
        "status": "reloaded",
        "model": current,
        "requested_by_user_id": current_user.id,
        "payload": payload or {},
    }


@router.get(
    "/integrations/status",
    summary="Check MLOps integration status",
    responses={
        200: {"description": "Integration status for Databricks, Snowflake and MLflow."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can inspect integrations."},
    },
)
def integrations_status(
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    databricks_status = DatabricksClient().health_check()
    snowflake_status = SnowflakeClient().health_check()
    mlflow_runs = len(MLflowClient().list_runs())
    return {
        "databricks": databricks_status,
        "snowflake": snowflake_status,
        "mlflow": {"mode": "local-wrapper", "logged_runs": mlflow_runs, "status": "ok"},
    }


@router.post(
    "/train-and-promote",
    response_model=TrainAndPromoteResponse,
    summary="Train and optionally promote a model",
    responses={
        200: {"description": "Training completed and promotion decision returned."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can train models."},
        422: {"description": "Invalid training request."},
    },
)
def train_and_promote_endpoint(
    payload: TrainModelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    orchestrator = MLOrchestrator(use_local_services=True)
    result = orchestrator.train_and_optionally_promote(payload.model_dump())
    current = get_current_model()

    db_run = TrainingRun(
        run_id=result.run_id,
        status="completed",
        dataset_uri=payload.dataset_uri,
        model_id=result.model_id,
        model_version=current.get("version"),
        metrics=result.metrics,
        parameters=payload.model_dump().get("parameters", {}),
        created_by_user_id=current_user.id,
    )
    db.add(db_run)
    db.commit()

    return {
        "run_id": result.run_id,
        "model_id": result.model_id,
        "promoted": result.promoted,
        "promotion_reason": result.promotion_reason,
        "metrics": result.metrics,
    }


@router.get("/runs")
def get_runs(
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    return {"items": list_training_runs()}


@router.post(
    "/drift/evaluate",
    summary="Evaluate production data drift",
    description=(
        "Compares recent production inference features against the current production model baseline. "
        "When trigger_retraining is true, a retraining job is submitted only if drift exceeds the configured threshold."
    ),
    responses={
        200: {"description": "Drift report generated."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can evaluate model drift."},
    },
)
def evaluate_drift_endpoint(
    trigger_retraining: bool = False,
    window_hours: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    return evaluate_data_drift(db=db, window_hours=window_hours, trigger_retraining=trigger_retraining)


@router.get(
    "/drift/reports",
    summary="List data drift reports",
    responses={
        200: {"description": "Stored drift reports."},
        401: {"description": "Missing or invalid JWT."},
        403: {"description": "Only ml_engineer and admin roles can inspect drift reports."},
    },
)
def get_drift_reports(
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    return {"items": list_drift_reports()}


@router.get("/runs/{run_id}")
def get_run_detail(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
    run = db.query(TrainingRun).filter(TrainingRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Training run not found: {run_id}")

    return {
        "run_id": run.run_id,
        "status": run.status,
        "dataset_uri": run.dataset_uri,
        "model_id": run.model_id,
        "model_version": run.model_version,
        "metrics": run.metrics,
        "parameters": run.parameters,
        "created_by_user_id": run.created_by_user_id,
        "created_at": run.created_at,
    }


@router.post("/{model_id}/promote")
def promote_model(
    model_id: str,
    current_user: User = Depends(require_roles("admin")),
):
    try:
        promoted = promote_model_to_production(model_id)
        return {"model_id": model_id, "stage": promoted["stage"], "promoted_at": promoted["promoted_at"]}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
