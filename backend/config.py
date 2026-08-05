"""Application configuration.

The MVP deliberately keeps configuration small. Secrets will be introduced only
when the LLM provider adapter is added in the next milestone.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "OpenSAP Copilot API"
    app_version: str = "0.1.0"
    environment: str = os.getenv("APP_ENV", "development")
    max_upload_size_bytes: int = int(
        os.getenv("MAX_UPLOAD_SIZE_BYTES", "200000")
    )


settings = Settings()
