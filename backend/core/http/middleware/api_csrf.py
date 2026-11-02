"""CSRF on every unsafe API request (architecture.md §5.2, security.md §4.1).

Ninja exempts its views from Django's CSRF middleware and checks CSRF only inside its own
cookie-auth classes, which this project doesn't use. So the check is applied here, before
any view runs, to every POST/PUT/PATCH/DELETE under /api/ — logged in or not (login and
sign-up need it too). The SPA reads the `csrftoken` cookie and sends `X-CSRFToken`.
"""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from ninja.utils import check_csrf

from core.http.problems import problem_response

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


class ApiCsrfMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if _needs_check(request) and check_csrf(request) is not None:
            return problem_response(
                request,
                status=403,
                code="csrf_failed",
                title="Your session needs refreshing",
                detail="Missing or invalid CSRF token. Reload the page and try again.",
            )
        return self.get_response(request)


def _needs_check(request: HttpRequest) -> bool:
    return request.path.startswith("/api/") and request.method not in _SAFE_METHODS
