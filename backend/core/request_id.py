"""The id of the request being handled, so every log line can be traced back to it."""

import uuid
from contextvars import ContextVar, Token

# Where the middleware also keeps the id on the request, for log lines written after it ends
REQUEST_META_KEY = "REQUEST_ID"

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    return _request_id.get()


def new_request_id() -> str:
    return uuid.uuid4().hex


def current_or_new_request_id() -> str:
    """Outside the middleware (tests, management commands) a fresh id still traces the work."""
    return current_request_id() or new_request_id()


def bind_request_id(request_id: str) -> Token[str | None]:
    return _request_id.set(request_id)


def unbind_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)
