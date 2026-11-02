import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.http import Http404, HttpRequest
from ninja import NinjaAPI, Schema
from ninja.testing import TestClient
from pydantic import ConfigDict

from core.errors import Conflict, NotFound
from core.http.areas import TeacherArea
from core.http.problems import CONTENT_TYPE, register_problem_handlers


class EntryClosed(Conflict):
    code = "entry_closed"
    title = "Entry to this test has closed"


class LoginIn(Schema):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str


api = NinjaAPI(urls_namespace="problems-test")
register_problem_handlers(api)


@api.get("/entry")
def entry(request: HttpRequest) -> None:
    closed_at = datetime(2026, 11, 12, 4, 40, tzinfo=UTC)
    raise EntryClosed("The late-entry window ended.", context={"closed_at": closed_at})


@api.get("/missing")
def missing(request: HttpRequest) -> None:
    raise NotFound("attempt")


@api.get("/django-404")
def django_404(request: HttpRequest) -> None:
    raise Http404


@api.get("/marks")
def marks(request: HttpRequest) -> None:
    raise Conflict(context={"score": Decimal("4.50")})


@api.get("/crash")
def crash(request: HttpRequest) -> None:
    raise RuntimeError("database password is hunter2")


@api.get("/admin-only", auth=TeacherArea())
def admin_only(request: HttpRequest) -> None:
    return None


@api.post("/login")
def login(request: HttpRequest, payload: LoginIn) -> None:
    return None


@api.get("/pages")
def pages(request: HttpRequest, page: int) -> None:
    return None


client = TestClient(api)


def problem(path: str, *, method: str = "get", **kwargs: object) -> tuple[int, dict[str, object]]:
    response = getattr(client, method)(path, **kwargs)
    assert response["Content-Type"] == CONTENT_TYPE
    return response.status_code, json.loads(response.content)


def test_domain_error_becomes_problem_json() -> None:
    status, body = problem("/entry")

    assert status == 409
    assert body["code"] == "entry_closed"
    assert body["type"] == "urn:problem:entry_closed"
    assert body["title"] == "Entry to this test has closed"
    assert body["detail"] == "The late-entry window ended."
    assert body["instance"] == "/entry"
    assert body["trace_id"]


def test_context_times_are_utc_with_z() -> None:
    _, body = problem("/entry")

    assert body["context"] == {"closed_at": "2026-11-12T04:40:00Z"}


def test_context_decimals_are_strings() -> None:
    _, body = problem("/marks")

    assert body["context"] == {"score": "4.50"}


def test_error_without_detail_uses_its_title() -> None:
    _, body = problem("/marks")

    assert body["detail"] == body["title"]
    assert "context" in body


@pytest.mark.parametrize("path", ["/missing", "/django-404"])
def test_not_found_has_one_shape(path: str) -> None:
    status, body = problem(path)

    assert status == 404
    assert body["code"] == "not_found"


def test_area_guard_failure_becomes_problem_json() -> None:
    status, body = problem("/admin-only")

    assert status == 401
    assert body["code"] == "not_authenticated"


def test_unknown_field_is_a_validation_error() -> None:
    status, body = problem(
        "/login", method="post", json={"email": "a@b.c", "password": "x", "admin": True}
    )

    assert status == 422
    assert body["code"] == "validation_error"
    assert body["errors"] == [
        {"field": "admin", "code": "extra_forbidden", "message": "Extra inputs are not permitted"}
    ]


def test_missing_body_field_is_named() -> None:
    _, body = problem("/login", method="post", json={"email": "a@b.c"})

    assert body["errors"][0]["field"] == "password"  # type: ignore[index]
    assert body["errors"][0]["code"] == "missing"  # type: ignore[index]


def test_bad_query_parameter_is_named() -> None:
    _, body = problem("/pages", query_params={"page": "first"})

    assert body["errors"][0]["field"] == "page"  # type: ignore[index]


def test_unexpected_error_hides_internals(caplog: pytest.LogCaptureFixture) -> None:
    status, body = problem("/crash")

    assert status == 500
    assert body["code"] == "internal_error"
    assert "hunter2" not in json.dumps(body)
    assert "hunter2" in caplog.text  # the details are in the log, for us
