import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings
from app.core.errors import PayloadTooLarge, error_response, internal_error_response
from app.core.logging import request_id

MAX_BODY_BYTES = 1_048_576

DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'"
STRICT_TRANSPORT_SECURITY = "max-age=63072000; includeSubDomains"

logger = logging.getLogger("examslot.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("x-request-id", "")
        current = incoming if _is_uuid(incoming) else str(uuid.uuid4())
        token = request_id.set(current)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = current
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "route": _route(request),
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            return response
        finally:
            request_id.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._production = settings.APP_ENV == "production"

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
        except Exception as error:
            logger.error("unhandled", extra={"error_type": type(error).__name__})
            response = internal_error_response()
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        if request.url.path not in DOCS_PATHS:
            response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        if self._production:
            response.headers["Strict-Transport-Security"] = STRICT_TRANSPORT_SECURITY
        if request.url.path.startswith("/api/v1"):
            response.headers["Cache-Control"] = "no-store"
        return response


class BodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            return error_response(PayloadTooLarge("PAYLOAD_TOO_LARGE"))
        return await call_next(request)


def add_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Retry-After", "X-Request-ID", "Content-Disposition"],
        max_age=600,
    )
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    app.add_middleware(RequestContextMiddleware)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _route(request: Request) -> str:
    if request.scope.get("route") is None:
        return "unmatched"
    path = request.url.path
    for name, value in (request.scope.get("path_params") or {}).items():
        path = path.replace(str(value), f"{{{name}}}")
    return path
