import logging
import sys
import uuid
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    """Injects the current request ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        return True


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


def setup_logging() -> None:
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL.upper())

    # Silence noisy libraries
    for name in ("httpx", "httpcore", "urllib3", "pymongo"):
        logging.getLogger(name).setLevel(logging.WARNING)
