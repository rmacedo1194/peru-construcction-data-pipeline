from __future__ import annotations

from pathlib import Path

import pytest

from app.lambda_app.config import Settings
from app.lambda_app.handler import lambda_handler
from app.lambda_app.models import (
    EventValidationError,
    FetchResult,
    IngestionEvent,
)
from app.lambda_app.storage import (
    FilesystemStorageWriter,
    S3StorageWriter,
    build_storage_paths,
    create_storage_writer,
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAW_BUCKET_NAME", "demo-raw-bucket")
    monkeypatch.setenv("RAW_PREFIX", "")
    monkeypatch.setenv("SOURCE_NAME", "peru-open-data")
    monkeypatch.setenv("REQUEST_TIMEOUT", "30")


def sample_event() -> dict[str, object]:
    return {
        "dataset_id": "licencias-construccion-lima",
        "resource_id": "dataset-page-html",
        "ingestion_id": "2026-04-03T10:00:00Z",
        "request": {
            "kind": "url",
            "url": "https://www.datosabiertos.gob.pe/dataset/licencias-de-construccion",
            "headers": {
                "Referer": "https://www.datosabiertos.gob.pe/dataset",
            },
        },
        "metadata": {
            "source_page": "https://www.datosabiertos.gob.pe/dataset",
            "notes": "Portal catalogue and dataset pages return HTML.",
        },
    }


def sample_fetch_result() -> FetchResult:
    return FetchResult(
        body=b"<html>ok</html>",
        final_url="https://www.datosabiertos.gob.pe/dataset/licencias-de-construccion",
        status_code=200,
        content_type="text/html; charset=utf-8",
        content_length=15,
        etag="etag-123",
        checksum_sha256="abc123",
        fetched_at="2026-04-03T10:00:04Z",
        response_headers={"Content-Type": "text/html; charset=utf-8"},
    )


def build_ingestion_event() -> IngestionEvent:
    return IngestionEvent.from_dict(
        sample_event(),
        default_source_id="peru-open-data",
        default_bucket="demo-raw-bucket",
        default_prefix="",
    )


def test_lambda_handler_success(monkeypatch: pytest.MonkeyPatch) -> None:
    puts: list[dict[str, object]] = []

    class FakeS3Client:
        def put_object(self, **kwargs):
            puts.append(kwargs)

    monkeypatch.setattr("app.lambda_app.handler.fetch_request", lambda request, settings: sample_fetch_result())
    monkeypatch.setattr("app.lambda_app.storage.create_s3_client", lambda: FakeS3Client())

    response = lambda_handler(sample_event(), None)

    assert response["status"] == "success"
    assert response["dataset_id"] == "licencias-construccion-lima"
    assert response["resource_id"] == "dataset-page-html"
    assert response["bucket"] == "demo-raw-bucket"
    assert response["raw_key"] == "peru-open-data/2026-04-03T10-00-00Z-dataset-page-html.html"
    assert len(puts) == 1
    assert puts[0]["Key"] == "peru-open-data/2026-04-03T10-00-00Z-dataset-page-html.html"


def test_event_validation_requires_ingestion_id() -> None:
    invalid_event = sample_event()
    invalid_event.pop("ingestion_id")

    with pytest.raises(EventValidationError):
        lambda_handler(invalid_event, None)


def test_build_storage_paths_is_deterministic_for_html_payloads() -> None:
    paths = build_storage_paths(build_ingestion_event(), sample_fetch_result())

    assert paths.bucket == "demo-raw-bucket"
    assert paths.raw_key == "peru-open-data/2026-04-03T10-00-00Z-dataset-page-html.html"


def test_create_storage_writer_uses_filesystem_backend(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("LOCAL_OUTPUT_DIR", str(tmp_path))

    writer = create_storage_writer(Settings.from_env())

    assert isinstance(writer, FilesystemStorageWriter)


def test_create_storage_writer_uses_s3_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = object()
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    monkeypatch.setattr("app.lambda_app.storage.create_s3_client", lambda: fake_client)

    writer = create_storage_writer(Settings.from_env())

    assert isinstance(writer, S3StorageWriter)
    assert writer._s3_client is fake_client


def test_filesystem_storage_writer_mirrors_s3_layout(tmp_path: Path) -> None:
    storage_paths = build_storage_paths(build_ingestion_event(), sample_fetch_result())
    writer = FilesystemStorageWriter(tmp_path)

    writer.write_raw_payload(storage_paths, sample_fetch_result())

    raw_path = tmp_path / storage_paths.bucket / Path(storage_paths.raw_key)

    assert raw_path.read_bytes() == b"<html>ok</html>"
