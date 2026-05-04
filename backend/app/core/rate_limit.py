"""Module level rate limiter singleton.

Module level so per route ``@limiter.limit(...)`` decorators can reference
a single ``Limiter`` instance from inside each router. ``build_app`` calls
:func:`reset_limiter` to clear in memory storage between fresh app builds
so tests do not leak counter state across cases.

The application wide cap (a per IP budget across every endpoint) is wired
via ``application_limits`` and reads the current env on every request,
so test fixtures that monkeypatch ``VEGA_RATE_LIMIT_DEFAULT`` before
calling ``build_app`` continue to work without reconstructing the
limiter.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import load_settings


def get_default_limit() -> str:
    """Return the per IP global cap from the current environment.

    Used as the dynamic ``application_limits`` callable so the limiter
    picks up changes to ``VEGA_RATE_LIMIT_DEFAULT`` at request time.
    """

    return load_settings().rate_limit_default


limiter = Limiter(
    key_func=get_remote_address,
    application_limits=[get_default_limit],
)


def reset_limiter() -> None:
    """Clear the limiter's in memory counters.

    Called from ``build_app`` so each fresh app starts with a clean slate.
    Tests call ``build_app`` per case via the ``client`` fixture, so this
    keeps per IP counters from leaking across tests.
    """

    limiter.reset()
