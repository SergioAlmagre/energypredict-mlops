from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.config import get_settings


class SnowflakeClient:
    """Hybrid Snowflake client: real query when configured, CSV fallback otherwise."""

    def __init__(self) -> None:
        settings = get_settings()
        self.account = settings.snowflake_account
        self.user = settings.snowflake_user
        self.password = settings.snowflake_password
        self.warehouse = settings.snowflake_warehouse
        self.database = settings.snowflake_database
        self.schema = settings.snowflake_schema
        self.role = settings.snowflake_role

    def is_configured(self) -> bool:
        required = [self.account, self.user, self.password, self.warehouse, self.database, self.schema]
        return all(bool(value) for value in required)

    def _connect(self):
        try:
            import snowflake.connector  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("snowflake-connector-python is not installed") from exc

        return snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            role=self.role,
        )

    def health_check(self) -> dict[str, Any]:
        if not self.is_configured():
            return {
                "mode": "stub",
                "configured": False,
                "status": "not_configured",
                "message": "Set SNOWFLAKE_* variables for real mode.",
            }

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT CURRENT_ACCOUNT(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
                account, warehouse, database, schema = cur.fetchone()

        return {
            "mode": "real",
            "configured": True,
            "status": "ok",
            "account": account,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
        }

    def load_sensor_data(self, dataset_uri: str = "data/synthetic_sensor_data.csv") -> pd.DataFrame:
        if self.is_configured() and dataset_uri.startswith("snowflake://"):
            query = "SELECT * FROM SENSOR_EVENTS_TRAINING"
            with self._connect() as conn:
                return pd.read_sql(query, conn)

        return pd.read_csv(dataset_uri)
