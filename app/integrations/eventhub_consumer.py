from __future__ import annotations

import json
import threading
from dataclasses import dataclass


class EventHubConsumerError(RuntimeError):
    pass


@dataclass(frozen=True)
class EventHubConsumerConfig:
    eventhub_name: str
    consumer_group: str = "$Default"
    connection_string: str | None = None
    fully_qualified_namespace: str | None = None
    max_batch_size: int = 50
    max_wait_time_seconds: int = 5


class EventHubBatchReader:
    def __init__(self, config: EventHubConsumerConfig) -> None:
        self._config = config

    def receive_batch(self) -> list[dict]:
        client = self._build_client()
        buffered_payloads: list[dict] = []
        finished = threading.Event()
        callback_error: Exception | None = None

        def on_event_batch(partition_context, events):  # noqa: ANN001
            nonlocal callback_error
            try:
                for event in events or []:
                    parsed = _event_to_payload(event)
                    if parsed is not None:
                        buffered_payloads.append(parsed)
                if buffered_payloads:
                    finished.set()
                    raise StopIteration()
            except StopIteration:
                raise
            except Exception as exc:  # pragma: no cover - defensive for provider callback internals
                callback_error = exc
                finished.set()
                raise

        try:
            try:
                client.receive_batch(
                    on_event_batch=on_event_batch,
                    max_batch_size=max(1, self._config.max_batch_size),
                    max_wait_time=max(1, self._config.max_wait_time_seconds),
                    starting_position="@latest",
                )
            except StopIteration:
                pass
        finally:
            try:
                client.close()
            except Exception:
                pass

        if callback_error:
            raise EventHubConsumerError(f"Event Hub callback failed: {callback_error}") from callback_error
        if not finished.is_set():
            return []
        return buffered_payloads

    def _build_client(self):
        try:
            from azure.eventhub import EventHubConsumerClient
        except Exception as exc:  # pragma: no cover - dependency may be optional in local setups
            raise EventHubConsumerError(
                "azure-eventhub is not installed. Add azure-eventhub to runtime dependencies."
            ) from exc

        if self._config.connection_string:
            return EventHubConsumerClient.from_connection_string(
                conn_str=self._config.connection_string,
                consumer_group=self._config.consumer_group,
                eventhub_name=self._config.eventhub_name,
            )

        if not self._config.fully_qualified_namespace:
            raise EventHubConsumerError(
                "Missing Event Hub connection. Set EVENTHUB_CONNECTION_STRING or EVENTHUB_FQ_NAMESPACE."
            )

        try:
            from azure.identity import DefaultAzureCredential
        except Exception as exc:  # pragma: no cover - dependency may be optional in local setups
            raise EventHubConsumerError(
                "azure-identity is not installed. Add azure-identity to runtime dependencies."
            ) from exc

        credential = DefaultAzureCredential()
        return EventHubConsumerClient(
            fully_qualified_namespace=self._config.fully_qualified_namespace,
            eventhub_name=self._config.eventhub_name,
            consumer_group=self._config.consumer_group,
            credential=credential,
        )


def _event_to_payload(event) -> dict | None:  # noqa: ANN001
    try:
        body_text = event.body_as_str(encoding="UTF-8")
    except Exception:
        try:
            body_text = bytes(event.body).decode("utf-8")
        except Exception:
            return None

    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None
    return payload
