"""Application settings loaded from environment variables.

Defaults are local development safe. Production overrides come from the
host's environment (Render service env vars in Phase 11).

Production hardening: when ``TRADER_ENVIRONMENT=production`` the loader
fails loud on a missing or wildcard ``TRADER_CORS_ORIGINS``. A wildcard
origin in production would defeat the threat model T8 protection
against arbitrary cross origin reads of the API. The loader also
rejects HTTP origins in production (HTTPS only) to keep MITM out of
scope. See ``docs/security/threat-model.md``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_CORS_ORIGINS = ("http://localhost:5173",)
DEFAULT_RATE_LIMIT = "60/minute"
DEFAULT_MAX_BODY_BYTES = 32 * 1024
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENVIRONMENT = "development"


class ConfigError(RuntimeError):
    """Raised at startup when production env is missing or unsafe.

    Catching ``RuntimeError`` upstream is intentional: a misconfigured
    production service must crash loudly at boot, not silently fall
    back to insecure defaults.
    """


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

    settings = Settings(
        cors_origins=origins,
        rate_limit_default=rate_limit,
        max_body_bytes=max_body,
        log_level=log_level,
        environment=environment,
    )

    if settings.is_production:
        _validate_production(settings)

    return settings


def _validate_production(settings: Settings) -> None:
    raw = os.environ.get("TRADER_CORS_ORIGINS", "").strip()
    if not raw:
        raise ConfigError(
            "TRADER_CORS_ORIGINS must be set explicitly in production. "
            "Refusing to fall back to localhost. See docs/setup-guide.md."
        )

    for origin in settings.cors_origins:
        if origin == "*":
            raise ConfigError(
                "TRADER_CORS_ORIGINS=* is not allowed in production. "
                "Set the exact frontend origin (e.g., https://trader.pages.dev)."
            )
        if not origin.startswith("https://"):
            raise ConfigError(
                "TRADER_CORS_ORIGINS must use https in production. "
                f"Got non https origin: {origin!r}."
            )
