from time import perf_counter
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.logging_config import set_request_id, reset_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request start/completion with a request id."""

    def __init__(self, app):
        super().__init__(app)
        self.access_logger = logging.getLogger("app.access")
        self.app_logger = logging.getLogger("app.main")

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request_id_token = set_request_id(request_id)
        start = perf_counter()
        status_code = 500

        self.access_logger.info(
            "http request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "-",
                "user_agent": request.headers.get("user-agent", "-"),
            },
        )

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["x-request-id"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            response.headers["Cache-Control"] = "no-store"
            return response
        except Exception:
            self.app_logger.exception(
                "http request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "client_ip": request.client.host if request.client else "-",
                    "user_agent": request.headers.get("user-agent", "-"),
                },
            )
            raise
        finally:
            duration_ms = round((perf_counter() - start) * 1000, 2)
            self.access_logger.info(
                "http request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": request.client.host if request.client else "-",
                    "user_agent": request.headers.get("user-agent", "-"),
                },
            )
            reset_request_id(request_id_token)
