"""JSON log lines on stdout, one object per line, tagged with the request id.

The host (Docker, Render) collects stdout. Values under secret-looking keys are
replaced, so passwords, codes and session ids never reach the logs (security.md §6).
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from core.request_id import REQUEST_META_KEY, current_request_id

REDACTED = "[redacted]"
# A key containing any of these words is treated as secret
_SECRET_WORDS = ("password", "secret", "token", "otp", "session", "answer", "cookie")
# Attributes every LogRecord has; anything else was passed through `extra=`
_RECORD_ATTRS = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": current_request_id() or _request_id_of(record),
            **redact(_extra_fields(record)),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str, ensure_ascii=False)


def redact(fields: dict[str, object]) -> dict[str, object]:
    """Replace the values of secret-looking keys."""
    return {key: REDACTED if _is_secret_key(key) else value for key, value in fields.items()}


def logging_config(level: str = "INFO") -> dict[str, Any]:
    """Django's LOGGING setting: everything, Django's own loggers included, as JSON."""
    handler = {"handlers": ["stdout"], "level": level, "propagate": False}
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json",
            },
        },
        "root": {"handlers": ["stdout"], "level": level},
        "loggers": {"django": handler, "django.server": handler},
    }


def _extra_fields(record: logging.LogRecord) -> dict[str, object]:
    return {key: value for key, value in vars(record).items() if key not in _RECORD_ATTRS}


def _request_id_of(record: logging.LogRecord) -> str | None:
    # Django logs some lines (e.g. "Not Found") after the middleware has finished;
    # those records carry the request, which still holds its id
    request = getattr(record, "request", None)
    meta = getattr(request, "META", {})
    request_id = meta.get(REQUEST_META_KEY) if isinstance(meta, dict) else None
    return request_id if isinstance(request_id, str) else None


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(word in lowered for word in _SECRET_WORDS)
