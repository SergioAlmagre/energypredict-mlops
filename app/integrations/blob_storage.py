from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class BlobStorageUnavailable(RuntimeError):
    pass


def _client():
    settings = get_settings()
    try:
        from azure.storage.blob import BlobServiceClient
    except Exception as exc:  # pragma: no cover - depends on optional package install
        raise BlobStorageUnavailable("azure-storage-blob is not installed") from exc

    if settings.azure_storage_connection_string:
        return BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)

    if settings.azure_storage_account_url:
        try:
            from azure.identity import DefaultAzureCredential
        except Exception as exc:  # pragma: no cover - depends on optional package install
            raise BlobStorageUnavailable("azure-identity is not installed") from exc
        return BlobServiceClient(account_url=settings.azure_storage_account_url, credential=DefaultAzureCredential())

    raise BlobStorageUnavailable("Azure Storage is not configured")


def is_blob_configured() -> bool:
    settings = get_settings()
    return bool(settings.azure_storage_connection_string or settings.azure_storage_account_url)


def read_json(container: str, blob_name: str) -> dict[str, Any] | None:
    blob = _client().get_blob_client(container=container, blob=blob_name)
    try:
        return json.loads(blob.download_blob().readall().decode("utf-8"))
    except Exception:
        return None


def write_json(container: str, blob_name: str, payload: dict[str, Any]) -> None:
    blob = _client().get_blob_client(container=container, blob=blob_name)
    blob.upload_blob(json.dumps(payload, indent=2), overwrite=True)


def upload_file(container: str, blob_name: str, source_path: Path) -> str:
    blob = _client().get_blob_client(container=container, blob=blob_name)
    with source_path.open("rb") as handle:
        blob.upload_blob(handle, overwrite=True)
    return f"azureblob://{container}/{blob_name}"


def download_file_uri(uri: str) -> Path:
    if not uri.startswith("azureblob://"):
        return Path(uri)

    container, blob_name = uri.removeprefix("azureblob://").split("/", 1)
    blob = _client().get_blob_client(container=container, blob=blob_name)
    suffix = Path(blob_name).suffix
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp.write(blob.download_blob().readall())
    temp.close()
    return Path(temp.name)
