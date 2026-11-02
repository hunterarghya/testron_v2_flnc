from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Status

from modules.identity.http_sessions import end_session


def get_csrf_cookie(request: HttpRequest) -> Status[None]:
    """Sets the `csrftoken` cookie the SPA echoes on every unsafe request (SPA boot)."""
    get_token(request)
    return Status(204, None)


def log_out(request: HttpRequest) -> Status[None]:
    end_session(request)
    return Status(204, None)
