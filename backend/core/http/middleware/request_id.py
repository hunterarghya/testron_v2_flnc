"""Give every request an id, send it back in a header, and tag its log lines with it."""

import re
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from core.request_id import REQUEST_META_KEY, bind_request_id, new_request_id, unbind_request_id

HEADER = "X-Request-ID"
# An id from the proxy (Caddy, Render) is kept, so one request can be followed across
# both logs. Anything else is replaced, so a client can't inject text into our logs.
_SAFE_ID = re.compile(r"[A-Za-z0-9._-]{8,128}")


class RequestIdMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = _incoming_id(request) or new_request_id()
        request.META[REQUEST_META_KEY] = request_id
        token = bind_request_id(request_id)
        try:
            response = self.get_response(request)
        finally:
            unbind_request_id(token)
        response[HEADER] = request_id
        return response


def _incoming_id(request: HttpRequest) -> str | None:
    candidate = request.headers.get(HEADER, "")
    return candidate if _SAFE_ID.fullmatch(candidate) else None
