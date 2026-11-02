"""The id of the request being handled, so every log line can be traced back to it."""

from contextvars import ContextVar, Token

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    return _request_id.get()


def bind_request_id(request_id: str) -> Token[str | None]:
    return _request_id.set(request_id)


def unbind_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)
