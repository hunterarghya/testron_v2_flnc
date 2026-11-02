from datetime import UTC, datetime

import pytest
from django.test import RequestFactory
from pytest_django.fixtures import Settings as DjangoSettings

from core.clock import FrozenClock, use_clock
from core.context import ANONYMOUS
from core.http.context import ctx_from
from core.request_id import bind_request_id, unbind_request_id
from core.tests.http.actors import ACTIVE_STUDENT, RESOLVER, TEACHER, as_actor

NOON = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _test_resolver(settings: DjangoSettings) -> None:
    settings.ACTOR_RESOLVER = RESOLVER


def test_ctx_uses_the_actor_from_the_area_guard() -> None:
    request = as_actor(RequestFactory().get("/"), ACTIVE_STUDENT)
    request.auth = TEACHER  # type: ignore[attr-defined]  # set by Ninja after the guard

    assert ctx_from(request).actor == TEACHER


def test_ctx_resolves_the_actor_on_public_routes() -> None:
    request = as_actor(RequestFactory().get("/"), ACTIVE_STUDENT)

    assert ctx_from(request).actor == ACTIVE_STUDENT


def test_ctx_is_anonymous_without_a_session() -> None:
    assert ctx_from(RequestFactory().get("/")).actor == ANONYMOUS


def test_ctx_reads_now_from_the_active_clock() -> None:
    with use_clock(FrozenClock(NOON)):
        assert ctx_from(RequestFactory().get("/")).now == NOON


def test_ctx_carries_the_request_id() -> None:
    token = bind_request_id("req-12345678")
    try:
        assert ctx_from(RequestFactory().get("/")).request_id == "req-12345678"
    finally:
        unbind_request_id(token)
