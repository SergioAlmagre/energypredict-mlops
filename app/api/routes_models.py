from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.models import TrainingRun, User
from app.db.session import get_db
from app.integrations.databricks_client import DatabricksClient
from app.integrations.mlflow_client import MLflowClient
from app.integrations.snowflake_client import SnowflakeClient
from app.ml.service import get_current_model, list_training_runs, promote_model_to_production, train_model_service
from app.schemas.prediction import TrainAndPromoteResponse, TrainModelRequest, TrainModelResponse
from app.services.ml_orchestrator import MLOrchestrator

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/current")
def current_model(current_user: User = Depends(require_roles("consumer", "analyst", "ml_engineer", "admin"))):
    return get_current_model()


@router.post("/train", response_model=TrainModelResponse)
def train_model_endpoint(
    payload: TrainModelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ml_engineer", "admin")),
):
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


@router.post("/train/remote")
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


@router.get("/integrations/status")
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


@router.post("/train-and-promote", response_model=TrainAndPromoteResponse)
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
