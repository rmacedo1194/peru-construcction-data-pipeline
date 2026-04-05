from __future__ import annotations

import json
import logging
from typing import Any

from .config import Settings
from .download import fetch_request
from .models import EventValidationError, IngestionEvent
from .storage import build_manifest, build_storage_paths, create_storage_writer

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda entry point for one trusted raw-ingestion request.
    """

    settings = Settings.from_env()
    ingestion_event = IngestionEvent.from_dict(
        event,
        default_source_id=settings.source_name,
        default_bucket=settings.raw_bucket_name,
        default_prefix=settings.raw_prefix,
    )

    LOGGER.info(
        json.dumps(
            {
                "message": "Starting raw ingestion",
                "source_id": ingestion_event.source_id,
                "dataset_id": ingestion_event.dataset_id,
                "resource_id": ingestion_event.resource_id,
                "ingestion_id": ingestion_event.ingestion_id,
                "request_url": ingestion_event.request.url,
            }
        )
    )

    try:
        fetch_result = fetch_request(ingestion_event.request, settings)
        storage_paths = build_storage_paths(ingestion_event, fetch_result)
        manifest = build_manifest(
            event=ingestion_event,
            fetch_result=fetch_result,
            storage_paths=storage_paths,
        )

        storage_writer = create_storage_writer(settings)
        storage_writer.write_raw_payload(storage_paths, fetch_result)
        storage_writer.write_manifest(storage_paths, manifest)
    except EventValidationError:
        raise
    except Exception:
        LOGGER.exception(
            "Raw ingestion failed for source=%s dataset=%s resource=%s ingestion_id=%s",
            ingestion_event.source_id,
            ingestion_event.dataset_id,
            ingestion_event.resource_id,
            ingestion_event.ingestion_id,
        )
        raise

    LOGGER.info(
        json.dumps(
            {
                "message": "Raw ingestion completed",
                "bucket": storage_paths.bucket,
                "raw_key": storage_paths.raw_key,
                "manifest_key": storage_paths.manifest_key,
                "http_status": fetch_result.status_code,
                "content_type": fetch_result.content_type,
            }
        )
    )

    return {
        "status": "success",
        "source_id": ingestion_event.source_id,
        "dataset_id": ingestion_event.dataset_id,
        "resource_id": ingestion_event.resource_id,
        "ingestion_id": ingestion_event.ingestion_id,
        "bucket": storage_paths.bucket,
        "raw_key": storage_paths.raw_key,
        "manifest_key": storage_paths.manifest_key,
        "http_status": fetch_result.status_code,
        "content_type": fetch_result.content_type,
    }
