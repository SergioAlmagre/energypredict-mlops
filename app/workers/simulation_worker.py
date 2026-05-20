from __future__ import annotations

import random
import threading
from dataclasses import dataclass
from time import sleep

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.eventhub_consumer import EventHubBatchReader, EventHubConsumerConfig, EventHubConsumerError
from app.services.streaming_service import get_or_create_simulation_state, ingest_telemetry_event


@dataclass(frozen=True)
class AssetProfile:
    asset_code: str
    temperature_base: float
    pressure_base: float
    vibration_base: float
    flow_rate_base: float
    energy_base: float
    operating_hours_base: float


class SimulationWorker:
    def __init__(self) -> None:
        settings = get_settings()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._random = random.Random()
        self._asset_profiles = self._build_profiles(settings)
        self._eventhub_reader = self._build_eventhub_reader(settings)
        self._stream_source = "eventhub" if self._eventhub_reader else "simulation"

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="energypredict-ingestion-worker", daemon=True)
        self._thread.start()

    def stop(self, timeout_seconds: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout_seconds)

    def _run(self) -> None:
        settings = get_settings()
        interval = max(1, settings.prediction_loop_interval_seconds)

        while not self._stop_event.is_set():
            should_sleep = True
            try:
                with SessionLocal() as db:
                    state = get_or_create_simulation_state(db)
                    if state.is_running:
                        if self._stream_source == "eventhub":
                            ingested_count = self._ingest_eventhub_batch(db)
                            should_sleep = ingested_count == 0
                        else:
                            profile = self._random.choice(self._asset_profiles)
                            ingest_telemetry_event(
                                db,
                                telemetry=self._generate_payload(profile),
                                source="simulation",
                                trace_id="simulation-worker",
                            )
                            should_sleep = False
            except Exception:
                # Keep worker resilient and retry on next cycle.
                pass

            if self._stop_event.is_set():
                break
            sleep(interval if should_sleep else max(1, interval // 2))

    def _build_profiles(self, settings) -> list[AssetProfile]:  # noqa: ANN001
        codes = [c.strip() for c in settings.simulation_asset_codes.split(",") if c.strip()]
        if not codes:
            codes = ["PUMP-001"]

        profiles: list[AssetProfile] = []
        for idx, code in enumerate(codes):
            profiles.append(
                AssetProfile(
                    asset_code=code,
                    temperature_base=78 + (idx * 4.5),
                    pressure_base=6.5 + (idx * 0.2),
                    vibration_base=1.0 + (idx * 0.45),
                    flow_rate_base=95 + (idx * 14),
                    energy_base=260 + (idx * 42),
                    operating_hours_base=1200 + (idx * 340),
                )
            )
        return profiles

    def _generate_payload(self, profile: AssetProfile) -> dict:
        return {
            "asset_code": profile.asset_code,
            "temperature": round(profile.temperature_base + self._random.uniform(-8.0, 15.0), 2),
            "pressure": round(max(0.2, profile.pressure_base + self._random.uniform(-1.0, 1.4)), 3),
            "vibration": round(max(0.0, profile.vibration_base + self._random.uniform(-0.4, 2.5)), 3),
            "flow_rate": round(max(0.0, profile.flow_rate_base + self._random.uniform(-25.0, 30.0)), 2),
            "energy_consumption": round(max(0.0, profile.energy_base + self._random.uniform(-90.0, 120.0)), 2),
            "operating_hours": round(profile.operating_hours_base + self._random.uniform(0.5, 3.2), 2),
        }

    def _build_eventhub_reader(self, settings) -> EventHubBatchReader | None:  # noqa: ANN001
        if not settings.eventhub_name:
            return None
        if not settings.eventhub_connection_string and not settings.eventhub_fq_namespace:
            return None

        return EventHubBatchReader(
            EventHubConsumerConfig(
                connection_string=settings.eventhub_connection_string,
                fully_qualified_namespace=settings.eventhub_fq_namespace,
                eventhub_name=settings.eventhub_name,
                consumer_group=settings.eventhub_consumer_group,
                max_batch_size=max(1, settings.eventhub_receive_batch_size),
                max_wait_time_seconds=max(1, settings.eventhub_receive_max_wait_seconds),
            )
        )

    def _ingest_eventhub_batch(self, db) -> int:  # noqa: ANN001
        if not self._eventhub_reader:
            return 0
        try:
            events = self._eventhub_reader.receive_batch()
        except EventHubConsumerError:
            return 0
        count = 0
        for telemetry in events:
            try:
                ingest_telemetry_event(
                    db,
                    telemetry=telemetry,
                    source="eventhub",
                    trace_id="eventhub-worker",
                )
                count += 1
            except Exception:
                continue
        return count


simulation_worker = SimulationWorker()
