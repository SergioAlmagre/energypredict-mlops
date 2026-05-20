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

    model_config = ConfigDict(extra="forbid")


class PredictionResponse(BaseModel):
    prediction_id: str
    asset_code: str
    risk_level: Literal["low", "medium", "high"]
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    model_name: str
    model_version: str
    created_at: datetime


class TrainModelRequest(BaseModel):
    dataset_uri: str = "data/synthetic_sensor_data.csv"
    algorithm: str = "RandomForestClassifier"
    register_model: bool = True
    parameters: dict[str, float | int | str | bool] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


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
