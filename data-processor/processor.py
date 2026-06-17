from __future__ import annotations

import os
import time

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.eventhub_consumer import EventHubBatchReader, EventHubConsumerConfig
from app.services.streaming_service import ingest_telemetry_event


def main() -> None:
    settings = get_settings()
    if not settings.stream_ingestion_enabled:
        while True:
            time.sleep(60)

    if not settings.eventhub_name or not (settings.eventhub_connection_string or settings.eventhub_fq_namespace):
        while True:
            time.sleep(60)

    reader = EventHubBatchReader(
        EventHubConsumerConfig(
            connection_string=settings.eventhub_connection_string,
            fully_qualified_namespace=settings.eventhub_fq_namespace,
            eventhub_name=settings.eventhub_name or "",
            consumer_group=settings.eventhub_consumer_group,
            max_batch_size=settings.eventhub_receive_batch_size,
            max_wait_time_seconds=settings.eventhub_receive_max_wait_seconds,
        )
    )
    sleep_seconds = int(os.getenv("PROCESSOR_IDLE_SLEEP_SECONDS", "5"))
    while True:
        with SessionLocal() as db:
            for telemetry in reader.receive_batch():
                ingest_telemetry_event(db, telemetry=telemetry, source="data-processor", trace_id="data-processor")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
