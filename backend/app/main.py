"""FastAPI application factory.

``build_app`` returns a fresh app each call so middleware state and the
rate limiter do not leak across tests. The module level ``app`` is what
``uvicorn app.main:app`` serves in production.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.backtest import router as backtest_router
from app.api.calculations import router as calculations_router
from app.api.heatmap import router as heatmap_router
from app.api.price import router as price_router
from app.api.tickers import router as tickers_router
from app.core.config import load_settings
from app.core.logging import configure_logging
from app.middleware import (
    AccessLogMiddleware,
    BodySizeLimitMiddleware,
    SecurityHeadersMiddleware,
)


def _rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded."},
    )


def _validation_handler(request: Request, exc: Exception) -> JSONResponse:
    # Strip the offending input value and any context: a 422 must never
    # echo user input or library internals back to the caller. See
    # docs/security/threat-model.md T11 (insufficient logging) and T8.
    if not isinstance(exc, RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Validation error."})
    errors = [
        {
            "loc": list(err.get("loc", [])),
            "msg": str(err.get("msg", "")),
            "type": str(err.get("type", "")),
        }
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


def build_app() -> FastAPI:
    settings = load_settings()
    configure_logging(level=settings.log_level)

    docs_url = None if settings.is_production else "/docs"
    openapi_url = None if settings.is_production else "/openapi.json"
    app = FastAPI(
        title="Trader Backend",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=None,
        openapi_url=openapi_url,
    )

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AccessLogMiddleware)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(price_router)
    app.include_router(heatmap_router)
    app.include_router(calculations_router)
    app.include_router(tickers_router)
    app.include_router(backtest_router)

    return app


app = build_app()
