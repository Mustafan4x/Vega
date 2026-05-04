"""Application settings loaded from environment variables.

Defaults are local development safe. Production overrides come from the
host's environment (Render service env vars in Phase 11).

All env var keys use the ``VEGA_*`` prefix.

Production hardening: when ``VEGA_ENVIRONMENT=production`` the loader
fails loud on a missing or wildcard ``VEGA_CORS_ORIGINS``. A wildcard
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


def read_env(name: str, default: str | None = None) -> str | None:
    """Read ``VEGA_<name>`` from the environment, returning ``default`` if unset.

    Kept as a tiny indirection so config call sites read by short
    name and the prefix is in one place.
    """

    return os.environ.get(f"VEGA_{name}", default)


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
    raw_origins = read_env("CORS_ORIGINS", "") or ""
    origins: tuple[str, ...] = tuple(o.strip() for o in raw_origins.split(",") if o.strip())
    if not origins:
        origins = DEFAULT_CORS_ORIGINS

    rate_limit = read_env("RATE_LIMIT_DEFAULT", DEFAULT_RATE_LIMIT) or DEFAULT_RATE_LIMIT

    raw_body = read_env("MAX_BODY_BYTES")
    max_body = int(raw_body) if raw_body else DEFAULT_MAX_BODY_BYTES

    log_level = read_env("LOG_LEVEL", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL
    environment = read_env("ENVIRONMENT", DEFAULT_ENVIRONMENT) or DEFAULT_ENVIRONMENT

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
    raw = (read_env("CORS_ORIGINS", "") or "").strip()
    if not raw:
        raise ConfigError(
            "VEGA_CORS_ORIGINS must be set explicitly in production. "
            "Refusing to fall back to localhost. See docs/setup-guide.md."
        )

    for origin in settings.cors_origins:
        if origin == "*":
            raise ConfigError(
                "VEGA_CORS_ORIGINS=* is not allowed in production. "
                "Set the exact frontend origin (e.g., https://vega.pages.dev)."
            )
        if not origin.startswith("https://"):
            raise ConfigError(
                f"VEGA_CORS_ORIGINS must use https in production. Got non https origin: {origin!r}."
            )
