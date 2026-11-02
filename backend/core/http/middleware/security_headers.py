"""Security headers on every response (architecture.md §5.15, security.md §4.3).

Django's SecurityMiddleware already sets HSTS (prod), nosniff and Referrer-Policy. This adds
the CSP, Permissions-Policy, and `Cache-Control: no-store` on the API, so no browser or proxy
keeps a copy of a student's data (api_contract.md §0).
"""

from collections.abc import Callable
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from core.http.csp import content_security_policy

PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=()"
# The interactive API docs (dev only) run their own inline scripts
_DOCS_PATH = "/api/v1/docs"


class SecurityHeadersMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path != _DOCS_PATH:
            response["Content-Security-Policy"] = content_security_policy(_spa_build_dir())
        response["Permissions-Policy"] = PERMISSIONS_POLICY
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store"
        return response


def _spa_build_dir() -> Path | None:
    directory: Path = settings.SPA_BUILD_DIR
    return directory if directory.is_dir() else None
