from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SensorEventResponse(BaseModel):
    id: str
    asset_code: str
    source: str
    event_ts: datetime
    telemetry_payload: dict
    risk_level: Literal["low", "medium", "high"]
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    created_at: datetime


class ActiveAlertResponse(BaseModel):
    id: str
    asset_code: str
    sensor_event_id: str
    severity: Literal["medium", "high"]
    status: Literal["active"]
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    message: str
    created_at: datetime
    updated_at: datetime


class SimulationControlResponse(BaseModel):
    is_running: bool
    last_started_at: datetime | None = None
    last_stopped_at: datetime | None = None
    updated_by_user_id: str | None = None
    updated_at: datetime
