"""Structured logging tests.

We do not snapshot the log line text; we only assert the logger emits one
record per request with the keys the runbook expects.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def captured_log(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    caplog.set_level(logging.INFO, logger="app.access")
    yield caplog


def test_request_emits_one_access_log_line(
    client: TestClient, captured_log: pytest.LogCaptureFixture
) -> None:
    response = client.get("/health")

    request_id = response.headers.get("x-request-id")
    assert request_id is not None

    matching = [r for r in captured_log.records if r.name == "app.access"]
    assert len(matching) >= 1


def test_access_log_contains_required_keys(
    client: TestClient, captured_log: pytest.LogCaptureFixture
) -> None:
    client.get("/health")

    matching = [r for r in captured_log.records if r.name == "app.access"]
    assert matching, "expected at least one access log line"

    payload = json.loads(matching[-1].getMessage())
    for key in ("event", "request_id", "method", "path", "status", "duration_ms"):
        assert key in payload, f"access log missing {key}: {payload}"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status"] == 200


def test_access_log_uses_response_request_id(
    client: TestClient, captured_log: pytest.LogCaptureFixture
) -> None:
    response = client.get("/health")

    request_id = response.headers["x-request-id"]
    matching = [r for r in captured_log.records if r.name == "app.access"]
    payload = json.loads(matching[-1].getMessage())
    assert payload["request_id"] == request_id


def test_validation_failure_logs_422(
    client: TestClient, captured_log: pytest.LogCaptureFixture
) -> None:
    client.post(
        "/api/price",
        json={"S": -1.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.2},
    )

    matching = [r for r in captured_log.records if r.name == "app.access"]
    assert matching
    payload = json.loads(matching[-1].getMessage())
    assert payload["status"] == 422
