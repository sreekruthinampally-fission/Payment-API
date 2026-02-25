import contextvars
import json
import logging
import logging.config
from datetime import datetime, timezone


request_id_ctx_var = contextvars.ContextVar("request_id", default="-")


class RequestContextFilter(logging.Filter):
    """Inject request-scoped fields into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Format logs as single-line JSON records."""

    def format(self, record: logging.LogRecord) -> str:
        standard_fields = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "asctime", "request_id", "taskName"
        }
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for field in ("method", "path", "status_code", "duration_ms", "client_ip", "user_agent"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Include any structured fields passed via logger extra={...}
        for key, value in record.__dict__.items():
            if key not in standard_fields and key not in payload and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=True)


def set_request_id(request_id: str):
    return request_id_ctx_var.set(request_id)


def reset_request_id(token):
    request_id_ctx_var.reset(token)


def setup_logging(log_level: str, log_format: str):
    format_name = "json" if log_format.lower() == "json" else "plain"
    level_name = log_level.upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {
                    "()": "app.logging_config.RequestContextFilter",
                }
            },
            "formatters": {
                "plain": {
                    "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                },
                "json": {
                    "()": "app.logging_config.JsonFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": format_name,
                    "filters": ["request_context"],
                }
            },
            "root": {
                "handlers": ["console"],
                "level": level_name,
            },
            "loggers": {
                "app": {
                    "level": level_name,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "app.access": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": level_name,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
