from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class EventValidationError(ValueError):
    """Raised when the Lambda event does not match the ingestion contract."""


@dataclass(frozen=True)
class IngestionRequest:
    kind: str
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: Any) -> "IngestionRequest":
        if not isinstance(value, dict):
            raise EventValidationError("event.request must be an object")

        kind = str(value.get("kind", "")).strip().lower()
        if kind != "url":
            raise EventValidationError("event.request.kind must be 'url'")

        url = str(value.get("url", "")).strip()
        if not url:
            raise EventValidationError("event.request.url is required")

        method = str(value.get("method", "GET")).strip().upper() or "GET"
        raw_headers = value.get("headers") or {}
        if not isinstance(raw_headers, dict):
            raise EventValidationError("event.request.headers must be an object when provided")

        headers = {
            str(header_name): str(header_value)
            for header_name, header_value in raw_headers.items()
        }

        return cls(kind=kind, url=url, method=method, headers=headers)


@dataclass(frozen=True)
class StorageTarget:
    bucket: str
    prefix: str = "raw"


@dataclass(frozen=True)
class IngestionEvent:
    source_id: str
    dataset_id: str
    resource_id: str
    ingestion_id: str
    request: IngestionRequest
    storage: StorageTarget
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        value: dict[str, Any],
        *,
        default_source_id: str,
        default_bucket: str,
        default_prefix: str,
    ) -> "IngestionEvent":
        if not isinstance(value, dict):
            raise EventValidationError("event must be an object")

        source_id = str(value.get("source_id") or default_source_id).strip()
        dataset_id = str(value.get("dataset_id") or value.get("dataset") or "").strip()
        resource_id = str(value.get("resource_id") or "").strip()
        ingestion_id = str(value.get("ingestion_id") or "").strip()

        if not source_id:
            raise EventValidationError("event.source_id is required")
        if not dataset_id:
            raise EventValidationError("event.dataset_id is required")
        if not resource_id:
            raise EventValidationError("event.resource_id is required")
        if not ingestion_id:
            raise EventValidationError("event.ingestion_id is required")

        parse_ingestion_id(ingestion_id)

        request = IngestionRequest.from_dict(value.get("request"))

        raw_storage = value.get("storage") or {}
        if not isinstance(raw_storage, dict):
            raise EventValidationError("event.storage must be an object when provided")

        bucket = str(raw_storage.get("bucket") or default_bucket).strip()
        prefix = str(raw_storage.get("prefix") or default_prefix).strip("/") or default_prefix
        if not bucket:
            raise EventValidationError("event.storage.bucket is required")

        metadata = value.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise EventValidationError("event.metadata must be an object when provided")

        return cls(
            source_id=source_id,
            dataset_id=dataset_id,
            resource_id=resource_id,
            ingestion_id=ingestion_id,
            request=request,
            storage=StorageTarget(bucket=bucket, prefix=prefix),
            metadata=metadata,
        )


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    final_url: str
    status_code: int
    content_type: str | None
    content_length: int | None
    etag: str | None
    checksum_sha256: str
    fetched_at: str
    response_headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StoragePaths:
    bucket: str
    raw_key: str
    manifest_key: str


@dataclass(frozen=True)
class IngestionManifest:
    source_id: str
    dataset_id: str
    resource_id: str
    ingestion_id: str
    requested_url: str
    final_url: str
    http_method: str
    http_status: int
    content_type: str | None
    content_length: int | None
    etag: str | None
    checksum_sha256: str
    fetched_at: str
    raw_s3_bucket: str
    raw_s3_key: str
    manifest_s3_key: str
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_ingestion_id(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
