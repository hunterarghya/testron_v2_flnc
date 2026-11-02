"""Every error leaves the API as RFC 9457 problem+json with a stable `code` (api_contract.md §1).

Registered once on the NinjaAPI. Controllers never catch errors; they arrive here.
"""

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from ninja import NinjaAPI
from ninja.errors import HttpError, ValidationError

from core.errors import DomainError, NotFound
from core.request_id import current_or_new_request_id

CONTENT_TYPE = "application/problem+json"
# Ninja raises its own HttpError for auth and CSRF failures
_HTTP_ERROR_CODES = {401: "not_authenticated", 403: "forbidden", 404: "not_found"}
# The request parts Ninja names first in an error location
_LOCATIONS = ("body", "query", "path", "header", "cookie", "form", "file")

logger = logging.getLogger(__name__)


def register_problem_handlers(api: NinjaAPI) -> None:
    api.add_exception_handler(DomainError, _domain_error)
    api.add_exception_handler(ValidationError, _validation_error)
    api.add_exception_handler(HttpError, _http_error)
    api.add_exception_handler(Http404, _not_found)
    api.add_exception_handler(Exception, _unexpected_error)


def problem_response(
    request: HttpRequest,
    *,
    status: int,
    code: str,
    title: str,
    detail: str | None = None,
    extra: Mapping[str, object] | None = None,
) -> HttpResponse:
    body: dict[str, object] = {
        "type": f"urn:problem:{code}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail or title,
        "instance": request.path,
        "trace_id": current_or_new_request_id(),
        **(extra or {}),
    }
    # DjangoJSONEncoder writes datetimes as ISO with Z and decimals as strings
    return JsonResponse(body, status=status, content_type=CONTENT_TYPE, encoder=DjangoJSONEncoder)


def _domain_error(request: HttpRequest, error: DomainError) -> HttpResponse:
    extra = {"context": error.context} if error.context else None
    return problem_response(
        request,
        status=error.status,
        code=error.code,
        title=error.title,
        detail=error.detail,
        extra=extra,
    )


def _validation_error(request: HttpRequest, error: ValidationError) -> HttpResponse:
    return problem_response(
        request,
        status=422,
        code="validation_error",
        title="Some fields are not valid",
        extra={"errors": [_field_error(item) for item in error.errors]},
    )


def _http_error(request: HttpRequest, error: HttpError) -> HttpResponse:
    code = _HTTP_ERROR_CODES.get(error.status_code, "http_error")
    return problem_response(request, status=error.status_code, code=code, title=str(error))


def _not_found(request: HttpRequest, error: Http404) -> HttpResponse:
    return _domain_error(request, NotFound())


def _unexpected_error(request: HttpRequest, error: Exception) -> HttpResponse:
    # The details go to the log only; the client gets the trace id to quote
    logger.exception("unhandled error", extra={"path": request.path})
    return problem_response(
        request, status=500, code="internal_error", title="Something went wrong on our side"
    )


def _field_error(item: Mapping[str, Any]) -> dict[str, str]:
    return {
        "field": _field_name(item.get("loc", ())),
        "code": str(item.get("type", "invalid")),
        "message": str(item.get("msg", "")),
    }


def _field_name(location: Sequence[object]) -> str:
    # ("body", "payload", "password") → "password"; ("query", "page") → "page"
    parts = [str(part) for part in location]
    if parts and parts[0] == "body":
        parts = parts[2:]
    elif parts and parts[0] in _LOCATIONS:
        parts = parts[1:]
    return ".".join(parts)
