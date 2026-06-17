from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PredictionRequest(BaseModel):
    asset_code: str = Field(..., min_length=1)
    temperature: float = Field(..., ge=-50, le=250)
    pressure: float = Field(..., gt=0, le=500)
    vibration: float = Field(..., ge=0, le=50)
    flow_rate: float = Field(..., ge=0)
    energy_consumption: float = Field(..., ge=0)
    operating_hours: float = Field(..., ge=0)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "asset_code": "PUMP-001",
                "temperature": 82.4,
                "pressure": 210.0,
                "vibration": 7.2,
                "flow_rate": 120.5,
                "energy_consumption": 450.0,
                "operating_hours": 5300.0,
            }
        },
    )


class PredictionResponse(BaseModel):
    prediction_id: str
    asset_code: str
    risk_level: Literal["low", "medium", "high"]
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    model_name: str
    model_version: str
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prediction_id": "8c1e67b9-5d6f-4275-9d32-b23b47cf64a6",
                "asset_code": "PUMP-001",
                "risk_level": "medium",
                "failure_probability": 0.42,
                "recommendation": "Schedule preventive inspection in the next 7 days.",
                "model_name": "asset_failure_classifier",
                "model_version": "2026.06.17.example",
                "created_at": "2026-06-17T10:30:00Z",
            }
        }
    )


class TrainModelRequest(BaseModel):
    dataset_uri: str = "data/synthetic_sensor_data.csv"
    algorithm: str = "RandomForestClassifier"
    register_model: bool = True
    parameters: dict[str, float | int | str | bool] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "dataset_uri": "azureblob://processed/latest/sensor_data.csv",
                "algorithm": "RandomForestClassifier",
                "register_model": True,
                "parameters": {"n_estimators": 120, "max_depth": 8, "random_state": 42},
            }
        },
    )


class TrainMetrics(BaseModel):
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)


class TrainedModelInfo(BaseModel):
    model_id: str
    name: str
    version: str
    artifact_uri: str
    algorithm: str
    registered: bool


class TrainModelResponse(BaseModel):
    run_id: str
    status: Literal["completed"]
    metrics: TrainMetrics
    model: TrainedModelInfo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "0f8274f7-37e6-407a-a890-0a5173576be6",
                "status": "completed",
                "metrics": {"accuracy": 0.94, "precision": 0.92, "recall": 0.91, "f1_score": 0.915},
                "model": {
                    "model_id": "example-production-model",
                    "name": "asset_failure_classifier",
                    "version": "2026.06.17.example",
                    "artifact_uri": "azureblob://models/asset_failure_classifier/2026.06.17.example/model.pkl",
                    "algorithm": "RandomForestClassifier",
                    "registered": True,
                },
            }
        }
    )


class TrainAndPromoteResponse(BaseModel):
    run_id: str
    model_id: str
    promoted: bool
    promotion_reason: str
    metrics: TrainMetrics


class RiskThresholdResponse(BaseModel):
    low_max: float = Field(..., ge=0.0, le=1.0)
    medium_max: float = Field(..., ge=0.0, le=1.0)
    updated_by_user_id: str | None = None
    updated_at: datetime


class RiskThresholdUpdateRequest(BaseModel):
    low_max: float = Field(..., ge=0.0, le=1.0)
    medium_max: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_order(self) -> "RiskThresholdUpdateRequest":
        if self.low_max >= self.medium_max:
            raise ValueError("low_max must be lower than medium_max")
        return self
