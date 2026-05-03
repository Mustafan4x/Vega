"""Application settings loaded from environment variables.

Defaults are local development safe. Production overrides come from the
host's environment (Render service env vars in Phase 11).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_CORS_ORIGINS = ("http://localhost:5173",)
DEFAULT_RATE_LIMIT = "60/minute"
DEFAULT_MAX_BODY_BYTES = 32 * 1024
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENVIRONMENT = "development"


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    rate_limit_default: str
    max_body_bytes: int
    log_level: str
    environment: str

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def load_settings() -> Settings:
    raw_origins = os.environ.get("TRADER_CORS_ORIGINS", "")
    origins: tuple[str, ...] = tuple(o.strip() for o in raw_origins.split(",") if o.strip())
    if not origins:
        origins = DEFAULT_CORS_ORIGINS

    rate_limit = os.environ.get("TRADER_RATE_LIMIT_DEFAULT", DEFAULT_RATE_LIMIT)

    raw_body = os.environ.get("TRADER_MAX_BODY_BYTES")
    max_body = int(raw_body) if raw_body else DEFAULT_MAX_BODY_BYTES

    log_level = os.environ.get("TRADER_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    environment = os.environ.get("TRADER_ENVIRONMENT", DEFAULT_ENVIRONMENT)

    return Settings(
        cors_origins=origins,
        rate_limit_default=rate_limit,
        max_body_bytes=max_body,
        log_level=log_level,
        environment=environment,
    )
