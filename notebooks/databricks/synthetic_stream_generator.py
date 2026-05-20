"""
EnergyPredict synthetic telemetry stream generator (Databricks/Event Hub).

Usage (Databricks notebook):
1) Attach this notebook/script to a cluster with internet egress.
2) Configure widgets or environment variables:
   - EVENTHUB_CONNECTION_STRING (preferred)
   - EVENTHUB_NAME (required with connection string)
3) Run continuously or by fixed event count.

This generator emits payloads compatible with backend ingestion contract:
{
  "event_id": "<uuid>",
  "event_ts": "2026-05-20T14:00:00Z",
  "asset_code": "PUMP-001",
  "temperature": 78.3,
  "pressure": 6.41,
  "vibration": 1.27,
  "flow_rate": 112.4,
  "energy_consumption": 338.9,
  "operating_hours": 2441.3,
  "anomaly": false,
  "source": "databricks"
}
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class AssetState:
    asset_code: str
    temperature: float
    pressure: float
    vibration: float
    flow_rate: float
    energy_consumption: float
    operating_hours: float


def _init_assets(num_assets: int, rng: random.Random) -> list[AssetState]:
    assets: list[AssetState] = []
    for idx in range(1, num_assets + 1):
        assets.append(
            AssetState(
                asset_code=f"PUMP-{idx:03d}",
                temperature=rng.uniform(64.0, 84.0),
                pressure=rng.uniform(4.8, 7.3),
                vibration=rng.uniform(0.20, 1.10),
                flow_rate=rng.uniform(90.0, 185.0),
                energy_consumption=rng.uniform(260.0, 460.0),
                operating_hours=rng.uniform(1000.0, 7000.0),
            )
        )
    return assets


def _next_payload(asset: AssetState, step: int, rng: random.Random, anomaly_probability: float) -> dict[str, Any]:
    season = math.sin(step / 12.0)
    asset.temperature = _clamp(asset.temperature + rng.uniform(-1.2, 1.4) + (season * 0.20), -50.0, 250.0)
    asset.pressure = _clamp(asset.pressure + rng.uniform(-0.10, 0.10), 0.2, 500.0)
    asset.vibration = _clamp(asset.vibration + rng.uniform(-0.05, 0.08), 0.0, 50.0)
    asset.flow_rate = _clamp(asset.flow_rate + rng.uniform(-3.5, 3.5), 0.0, 5000.0)
    asset.energy_consumption = _clamp(asset.energy_consumption + rng.uniform(-6.0, 9.0), 0.0, 10000.0)
    asset.operating_hours = _clamp(asset.operating_hours + rng.uniform(0.1, 2.0), 0.0, 120000.0)

    anomaly = rng.random() < anomaly_probability
    if anomaly:
        asset.temperature = _clamp(asset.temperature + rng.uniform(7.0, 22.0), -50.0, 250.0)
        asset.vibration = _clamp(asset.vibration + rng.uniform(0.5, 2.8), 0.0, 50.0)
        asset.pressure = _clamp(asset.pressure + rng.uniform(0.5, 2.4), 0.2, 500.0)
        asset.energy_consumption = _clamp(asset.energy_consumption + rng.uniform(18.0, 70.0), 0.0, 10000.0)

    return {
        "event_id": str(uuid.uuid4()),
        "event_ts": _utc_now_iso(),
        "asset_code": asset.asset_code,
        "temperature": round(asset.temperature, 3),
        "pressure": round(asset.pressure, 3),
        "vibration": round(asset.vibration, 4),
        "flow_rate": round(asset.flow_rate, 3),
        "energy_consumption": round(asset.energy_consumption, 3),
        "operating_hours": round(asset.operating_hours, 3),
        "anomaly": anomaly,
        "source": "databricks",
    }


def _create_eventhub_producer(
    connection_string: str | None,
    eventhub_name: str | None,
):
    if not connection_string:
        raise RuntimeError("EVENTHUB_CONNECTION_STRING is required for this generator.")
    if not eventhub_name:
        raise RuntimeError("EVENTHUB_NAME is required for this generator.")

    from azure.eventhub import EventHubProducerClient

    return EventHubProducerClient.from_connection_string(
        conn_str=connection_string,
        eventhub_name=eventhub_name,
    )


def generate_stream(
    *,
    connection_string: str | None,
    eventhub_name: str | None,
    num_assets: int,
    interval_seconds: float,
    anomaly_probability: float,
    seed: int,
    max_events: int,
    dry_run: bool,
) -> None:
    rng = random.Random(seed)
    assets = _init_assets(num_assets=num_assets, rng=rng)

    producer = None if dry_run else _create_eventhub_producer(connection_string, eventhub_name)
    sent = 0
    step = 1
    print(
        f"[{_utc_now_iso()}] Starting synthetic stream: "
        f"assets={num_assets}, interval={interval_seconds}s, anomaly_probability={anomaly_probability}, dry_run={dry_run}"
    )

    try:
        while max_events <= 0 or sent < max_events:
            for asset in assets:
                payload = _next_payload(asset, step=step, rng=rng, anomaly_probability=anomaly_probability)

                if dry_run:
                    print(json.dumps(payload, ensure_ascii=True))
                else:
                    from azure.eventhub import EventData

                    batch = producer.create_batch()
                    batch.add(EventData(json.dumps(payload, ensure_ascii=True)))
                    producer.send_batch(batch)
                    print(
                        f"[{_utc_now_iso()}] sent event_id={payload['event_id']} asset={payload['asset_code']} "
                        f"anomaly={payload['anomaly']}"
                    )

                sent += 1
                if 0 < max_events <= sent:
                    break
                time.sleep(interval_seconds)

            step += 1
    finally:
        if producer is not None:
            producer.close()
        print(f"[{_utc_now_iso()}] Stream completed. total_events={sent}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Databricks synthetic telemetry generator for Event Hub.")
    parser.add_argument("--eventhub-connection-string", default=None)
    parser.add_argument("--eventhub-name", default=None)
    parser.add_argument("--assets", type=int, default=5)
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    parser.add_argument("--anomaly-probability", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="0 means run continuously.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _read_widget(name: str, default: str = "") -> str:
    try:
        # Databricks runtime injects dbutils in notebook context.
        return dbutils.widgets.get(name)  # type: ignore[name-defined]  # noqa: F821
    except Exception:
        return default


def run_from_databricks_widgets() -> None:
    # Optional helper for Databricks notebooks.
    for widget_name, default in [
        ("eventhub_connection_string", ""),
        ("eventhub_name", ""),
        ("assets", "5"),
        ("interval_seconds", "1"),
        ("anomaly_probability", "0.10"),
        ("seed", "42"),
        ("max_events", "0"),
        ("dry_run", "false"),
    ]:
        try:
            dbutils.widgets.text(widget_name, default)  # type: ignore[name-defined]  # noqa: F821
        except Exception:
            pass

    dry_run_raw = _read_widget("dry_run", "false").strip().lower()
    generate_stream(
        connection_string=_read_widget("eventhub_connection_string", "") or None,
        eventhub_name=_read_widget("eventhub_name", "") or None,
        num_assets=int(_read_widget("assets", "5")),
        interval_seconds=float(_read_widget("interval_seconds", "1")),
        anomaly_probability=float(_read_widget("anomaly_probability", "0.10")),
        seed=int(_read_widget("seed", "42")),
        max_events=int(_read_widget("max_events", "0")),
        dry_run=dry_run_raw in {"1", "true", "yes", "y"},
    )


if __name__ == "__main__":
    args = _parse_args()
    generate_stream(
        connection_string=args.eventhub_connection_string,
        eventhub_name=args.eventhub_name,
        num_assets=args.assets,
        interval_seconds=args.interval_seconds,
        anomaly_probability=args.anomaly_probability,
        seed=args.seed,
        max_events=args.max_events,
        dry_run=args.dry_run,
    )
