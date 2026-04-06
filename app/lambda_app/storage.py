from __future__ import annotations

import mimetypes
import re
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from .config import Settings
from .models import FetchResult, IngestionEvent, StoragePaths, parse_ingestion_id

CONTENT_TYPE_EXTENSION_OVERRIDES = {
    "text/csv": ".csv",
    "text/html": ".html",
    "application/json": ".json",
    "application/xml": ".xml",
}


class StorageError(RuntimeError):
    """Raised when raw artifacts or manifests cannot be persisted."""


class StorageWriter:
    """Small interface so the handler can switch persistence backends by env."""

    def write_raw_payload(self, storage_paths: StoragePaths, fetch_result: FetchResult) -> None:
        raise NotImplementedError


def build_storage_paths(event: IngestionEvent, fetch_result: FetchResult) -> StoragePaths:
    ingested_at = parse_ingestion_id(event.ingestion_id)
    extension = detect_extension(fetch_result.final_url, fetch_result.content_type)
    # Keep the bronze layer easy to browse: one source folder and one dated file
    # per ingestion event instead of deep partition folders plus manifests.
    filename = (
        f"{ingested_at.strftime('%Y-%m-%dT%H-%M-%SZ')}"
        f"-{sanitize_path_segment(event.resource_id)}{extension}"
    )
    key_segments = [segment for segment in (event.storage.prefix, event.source_id, filename) if segment]
    base_key = "/".join(sanitize_path_segment(segment) for segment in key_segments[:-1])
    raw_key = f"{base_key}/{filename}" if base_key else filename
    return StoragePaths(
        bucket=event.storage.bucket,
        raw_key=raw_key,
    )


def create_s3_client():
    import boto3

    return boto3.client("s3")


class S3StorageWriter(StorageWriter):
    def __init__(self, s3_client) -> None:
        self._s3_client = s3_client

    def write_raw_payload(self, storage_paths: StoragePaths, fetch_result: FetchResult) -> None:
        try:
            extra_args: dict[str, str] = {}
            if fetch_result.content_type:
                extra_args["ContentType"] = fetch_result.content_type

            self._s3_client.put_object(
                Bucket=storage_paths.bucket,
                Key=storage_paths.raw_key,
                Body=fetch_result.body,
                **extra_args,
            )
        except Exception as exc:  # pragma: no cover - surfaced by handler tests
            raise StorageError(
                f"Unable to write raw payload to s3://{storage_paths.bucket}/{storage_paths.raw_key}: {exc}"
            ) from exc

class FilesystemStorageWriter(StorageWriter):
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def write_raw_payload(self, storage_paths: StoragePaths, fetch_result: FetchResult) -> None:
        target_path = self._root_dir / storage_paths.bucket / PurePosixPath(storage_paths.raw_key)
        self._write_bytes(target_path, fetch_result.body)

    def _write_bytes(self, target_path: Path, payload: bytes) -> None:
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(payload)
        except Exception as exc:  # pragma: no cover - surfaced by handler tests
            raise StorageError(f"Unable to write local artifact to {target_path}: {exc}") from exc


def create_storage_writer(settings: Settings) -> StorageWriter:
    if settings.storage_backend == "filesystem":
        return FilesystemStorageWriter(settings.local_output_dir)
    return S3StorageWriter(create_s3_client())


def sanitize_path_segment(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    compact = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_only.strip().lower()).strip("-._")
    return compact or "unknown"


def detect_extension(url: str, content_type: str | None) -> str:
    suffix = PurePosixPath(urlparse(url).path).suffix
    if suffix and len(suffix) <= 10:
        return suffix.lower()

    normalized_type = (content_type or "").split(";")[0].strip().lower()
    if normalized_type in CONTENT_TYPE_EXTENSION_OVERRIDES:
        return CONTENT_TYPE_EXTENSION_OVERRIDES[normalized_type]

    guessed = mimetypes.guess_extension(normalized_type) if normalized_type else None
    return guessed or ".bin"
