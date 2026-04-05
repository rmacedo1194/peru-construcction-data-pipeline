from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from urllib.request import Request, urlopen

from .config import Settings
from .models import FetchResult, IngestionRequest


class DownloadError(RuntimeError):
    """Raised when the source cannot be fetched successfully."""


def fetch_request(request: IngestionRequest, settings: Settings) -> FetchResult:
    headers = settings.default_request_headers()
    headers.update(request.headers)

    transport_request = Request(
        url=request.url,
        headers=headers,
        method=request.method,
    )

    try:
        with urlopen(transport_request, timeout=settings.request_timeout) as response:
            body = response.read()
            header_map = {key: value for key, value in response.headers.items()}
            content_type = response.headers.get("Content-Type")
            content_length_header = response.headers.get("Content-Length")
            content_length = int(content_length_header) if content_length_header else len(body)

            return FetchResult(
                body=body,
                final_url=response.geturl(),
                status_code=getattr(response, "status", 200),
                content_type=content_type,
                content_length=content_length,
                etag=response.headers.get("ETag"),
                checksum_sha256=hashlib.sha256(body).hexdigest(),
                fetched_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                response_headers=header_map,
            )
    except Exception as exc:  # pragma: no cover - exercised through tests with stubs
        raise DownloadError(f"Unable to fetch {request.url}: {exc}") from exc
