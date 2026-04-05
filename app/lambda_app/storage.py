from __future__ import annotations

import json
import mimetypes
import re
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from .config import Settings
from .models import FetchResult, IngestionEvent, IngestionManifest, StoragePaths, parse_ingestion_id

CONTENT_TYPE_EXTENSION_OVERRIDES = {
    "text/csv": ".csv",
    "text/html": ".html",
    "application/json": ".json",
    "application/xml": ".xml",
}
SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}


class StorageError(RuntimeError):
    """Raised when raw artifacts or manifests cannot be persisted."""


class StorageWriter:
    """Small interface so the handler can switch persistence backends by env."""

    def write_raw_payload(self, storage_paths: StoragePaths, fetch_result: FetchResult) -> None:
        raise NotImplementedError

    def write_manifest(self, storage_paths: StoragePaths, manifest: IngestionManifest) -> None:
        raise NotImplementedError


def build_storage_paths(event: IngestionEvent, fetch_result: FetchResult) -> StoragePaths:
    ingested_at = parse_ingestion_id(event.ingestion_id)
    # Deterministic keys make retries path-idempotent: the same ingestion identifiers
    # overwrite the same objects instead of creating duplicate raw artifacts.
    base_key = "/".join(
        [
            sanitize_path_segment(event.storage.prefix),
            sanitize_path_segment(event.source_id),
            sanitize_path_segment(event.dataset_id),
            sanitize_path_segment(event.resource_id),
            ingested_at.strftime("%Y"),
            ingested_at.strftime("%m"),
            ingested_at.strftime("%d"),
            sanitize_path_segment(event.ingestion_id),
        ]
    )
    extension = detect_extension(fetch_result.final_url, fetch_result.content_type)
    return StoragePaths(
        bucket=event.storage.bucket,
        raw_key=f"{base_key}/payload{extension}",
        manifest_key=f"{base_key}/manifest.json",
    )


def build_manifest(
    *,
    event: IngestionEvent,
    fetch_result: FetchResult,
    storage_paths: StoragePaths,
) -> IngestionManifest:
    return IngestionManifest(
        source_id=event.source_id,
        dataset_id=event.dataset_id,
        resource_id=event.resource_id,
        ingestion_id=event.ingestion_id,
        requested_url=event.request.url,
        final_url=fetch_result.final_url,
        http_method=event.request.method,
        http_status=fetch_result.status_code,
        content_type=fetch_result.content_type,
        content_length=fetch_result.content_length,
        etag=fetch_result.etag,
        checksum_sha256=fetch_result.checksum_sha256,
        fetched_at=fetch_result.fetched_at,
        raw_s3_bucket=storage_paths.bucket,
        raw_s3_key=storage_paths.raw_key,
        manifest_s3_key=storage_paths.manifest_key,
        request_headers=sanitize_headers(event.request.headers),
        response_headers=sanitize_headers(fetch_result.response_headers),
        source_metadata=event.metadata,
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

    def write_manifest(self, storage_paths: StoragePaths, manifest: IngestionManifest) -> None:
        try:
            self._s3_client.put_object(
                Bucket=storage_paths.bucket,
                Key=storage_paths.manifest_key,
                Body=json.dumps(manifest.to_dict(), sort_keys=True).encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as exc:  # pragma: no cover - surfaced by handler tests
            raise StorageError(
                f"Unable to write manifest to s3://{storage_paths.bucket}/{storage_paths.manifest_key}: {exc}"
            ) from exc


class FilesystemStorageWriter(StorageWriter):
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def write_raw_payload(self, storage_paths: StoragePaths, fetch_result: FetchResult) -> None:
        target_path = self._root_dir / storage_paths.bucket / PurePosixPath(storage_paths.raw_key)
        self._write_bytes(target_path, fetch_result.body)

    def write_manifest(self, storage_paths: StoragePaths, manifest: IngestionManifest) -> None:
        target_path = self._root_dir / storage_paths.bucket / PurePosixPath(storage_paths.manifest_key)
        payload = json.dumps(manifest.to_dict(), indent=2, sort_keys=True).encode("utf-8")
        self._write_bytes(target_path, payload)

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


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        header_name: header_value
        for header_name, header_value in headers.items()
        if header_name.lower() not in SENSITIVE_HEADERS
    }


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
