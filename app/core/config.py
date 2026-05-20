from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EnergyPredict MLOps API"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["dev", "prod"] = "dev"
    database_url: str = "sqlite:///./energypredict.db"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    jwt_issuer: str = "energypredict-api"
    cors_allowed_origins: str = "http://localhost:3000"
    default_model_name: str = "asset_failure_classifier"
    default_model_version: str = "1.0.0"
    login_rate_limit_requests: int = 10
    login_rate_limit_window_seconds: int = 60
    login_failed_attempts_limit: int = 5
    login_failed_attempts_window_seconds: int = 300
    predict_rate_limit_requests: int = 60
    predict_rate_limit_window_seconds: int = 60
    ml_api_base_url: str = "http://localhost:8000/api/v1"
    auto_promote_min_f1_score: float = 0.80
    risk_threshold_low_max_default: float = 0.35
    risk_threshold_medium_max_default: float = 0.70
    llm_provider: str = "disabled"
    llm_model: str = "gpt-4o-mini"
    llm_endpoint: str | None = None
    llm_api_key: str | None = None
    llm_timeout_seconds: int = 20
    llm_retry_attempts: int = 2
    llm_retry_backoff_seconds: float = 0.4
    llm_circuit_breaker_enabled: bool = True
    llm_circuit_breaker_failures: int = 5
    llm_circuit_breaker_reset_seconds: int = 120
    stream_ingestion_enabled: bool = False
    prediction_loop_interval_seconds: int = 10
    simulation_asset_codes: str = "PUMP-001,PUMP-002,TURBINE-001"
    eventhub_connection_string: str | None = None
    eventhub_fq_namespace: str | None = None
    eventhub_name: str | None = None
    eventhub_consumer_group: str = "$Default"
    eventhub_receive_batch_size: int = 50
    eventhub_receive_max_wait_seconds: int = 5
    databricks_workspace_url: str | None = None
    databricks_token: str | None = None
    databricks_job_id: int | None = None
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    snowflake_role: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_prod_security(self) -> "Settings":
        if self.environment == "prod" and self.jwt_secret_key in {"change-me", "change-me-dev-only"}:
            raise ValueError("JWT_SECRET_KEY must be set to a strong non-default value in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
