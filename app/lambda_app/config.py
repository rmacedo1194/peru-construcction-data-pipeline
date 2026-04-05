from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
DEFAULT_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
DEFAULT_ACCEPT_LANGUAGE = "es-PE,es;q=0.9,en;q=0.8"
SUPPORTED_STORAGE_BACKENDS = {"s3", "filesystem"}


@dataclass(frozen=True)
class Settings:
    """
    Environment-backed configuration for raw ingestion.
    """

    raw_bucket_name: str
    raw_prefix: str
    source_name: str
    request_timeout: int
    user_agent: str
    default_accept: str
    default_accept_language: str
    storage_backend: str
    local_output_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        raw_bucket_name = os.getenv("RAW_BUCKET_NAME", "").strip()
        if not raw_bucket_name:
            raise ValueError("Missing required environment variable: RAW_BUCKET_NAME")

        request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        if request_timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT must be a positive integer")

        storage_backend = os.getenv("STORAGE_BACKEND", "s3").strip().lower() or "s3"
        if storage_backend not in SUPPORTED_STORAGE_BACKENDS:
            supported = ", ".join(sorted(SUPPORTED_STORAGE_BACKENDS))
            raise ValueError(f"STORAGE_BACKEND must be one of: {supported}")

        return cls(
            raw_bucket_name=raw_bucket_name,
            raw_prefix=os.getenv("RAW_PREFIX", "raw").strip("/") or "raw",
            source_name=os.getenv("SOURCE_NAME", "peru-open-data").strip() or "peru-open-data",
            request_timeout=request_timeout,
            user_agent=os.getenv("REQUEST_USER_AGENT", DEFAULT_USER_AGENT).strip() or DEFAULT_USER_AGENT,
            default_accept=os.getenv("REQUEST_ACCEPT", DEFAULT_ACCEPT).strip() or DEFAULT_ACCEPT,
            default_accept_language=(
                os.getenv("REQUEST_ACCEPT_LANGUAGE", DEFAULT_ACCEPT_LANGUAGE).strip()
                or DEFAULT_ACCEPT_LANGUAGE
            ),
            storage_backend=storage_backend,
            local_output_dir=Path(os.getenv("LOCAL_OUTPUT_DIR", ".sam-local-output")).expanduser(),
        )

    def default_request_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": self.default_accept,
            "Accept-Language": self.default_accept_language,
        }
