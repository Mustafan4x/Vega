"""Logging configuration.

The access logger emits one JSON line per request. The body of each log
message is itself a JSON document so consumers (Render log aggregator,
log search tools) can parse it without a separate formatter.
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)

    access = logging.getLogger("app.access")
    access.setLevel(logging.INFO)
    access.propagate = True
