import os 
from dataclasses import dataclass

@dataclass(frozen=True)

class Settings:
    """
    Application settings loaded from environment variables.
    """
    api_base_url: str
    raw_bucket_name: str
    source_name : str
    request_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Build Settings from environment variables.
        """
        api_base_url = os.getenv("API_BASE_URL", "https://api.example.com")
        raw_bucket_name = os.getenv("RAW_BUCKET_NAME", "my-raw-bucket")
        source_name = os.getenv("SOURCE_NAME", "default_source")
        request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))

        if not api_base_url:
            raise ValueError("Missing required environment variable: API_BASE_URL")
        if not raw_bucket_name:
            raise ValueError("Missing required environment variable: RAW_BUCKET_NAME")
        return cls(
            api_base_url=api_base_url,
            raw_bucket_name=raw_bucket_name,
            source_name=source_name,
            request_timeout=request_timeout
        )

    


