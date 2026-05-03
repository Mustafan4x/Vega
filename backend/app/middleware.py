"""ASGI middleware for the Trader backend.

Three responsibilities, each in its own middleware class so the wiring in
``app.main.build_app`` reads top to bottom in the order the layers run:

* :class:`AccessLogMiddleware` generates a per request id, echoes it on the
  response as ``X-Request-Id``, and emits one JSON access log line at the
  end of the request.
* :class:`SecurityHeadersMiddleware` adds the response level security
  headers required by ``docs/security/threat-model.md`` T13 and strips any
  ``Server`` header to reduce fingerprinting.
* :class:`BodySizeLimitMiddleware` rejects requests whose ``Content-Length``
  exceeds ``settings.max_body_bytes`` with a 413 response, so an oversized
  body never reaches the JSON parser.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.types import Message, Receive, Scope, Send

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_SECURITY_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload"),
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (
        b"permissions-policy",
        b"camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    ),
    (b"content-security-policy", b"frame-ancestors 'none'"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cross-origin-resource-policy", b"same-site"),
)


class AccessLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._logger = logging.getLogger("app.access")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:16]
        status_holder: dict[str, int] = {"status": 500}

        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers = [(k, v) for k, v in headers if k.lower() != b"x-request-id"]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": headers}
                status_holder["status"] = int(message["status"])
            await send(message)

        start = time.perf_counter()
        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            payload = {
                "event": "access",
                "request_id": request_id,
                "method": scope.get("method", ""),
                "path": scope.get("path", ""),
                "status": status_holder["status"],
                "duration_ms": duration_ms,
            }
            self._logger.info(json.dumps(payload, separators=(",", ":")))


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {k.lower() for k, _ in headers}
                additions = [(k, v) for k, v in _SECURITY_HEADERS if k.lower() not in existing]
                headers.extend(additions)
                headers = [(k, v) for k, v in headers if k.lower() != b"server"]
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, wrapped_send)


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = 32 * 1024) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = -1
                if declared > self.max_bytes:
                    body = b'{"detail":"Request body too large."}'
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 413,
                            "headers": [
                                (b"content-type", b"application/json"),
                                (b"content-length", str(len(body)).encode("ascii")),
                            ],
                        }
                    )
                    await send({"type": "http.response.body", "body": body})
                    return
                break

        await self.app(scope, receive, send)
