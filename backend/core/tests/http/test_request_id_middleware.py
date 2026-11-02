import pytest
from django.http import HttpRequest, HttpResponse
from django.test import Client, RequestFactory

from core.http.middleware.request_id import HEADER, RequestIdMiddleware
from core.request_id import current_request_id

seen_ids: list[str | None] = []


def view(request: HttpRequest) -> HttpResponse:
    seen_ids.append(current_request_id())
    return HttpResponse("ok")


@pytest.fixture(autouse=True)
def _clear_seen_ids() -> None:
    seen_ids.clear()


def call(**headers: str) -> HttpResponse:
    request = RequestFactory().get("/", headers=headers)
    return RequestIdMiddleware(view)(request)


def test_new_id_is_generated_and_returned() -> None:
    response = call()

    assert len(response[HEADER]) == 32
    assert seen_ids == [response[HEADER]]


def test_each_request_gets_its_own_id() -> None:
    assert call()[HEADER] != call()[HEADER]


def test_proxy_id_is_kept() -> None:
    response = call(**{HEADER: "caddy-abc-123456"})

    assert response[HEADER] == "caddy-abc-123456"
    assert seen_ids == ["caddy-abc-123456"]


@pytest.mark.parametrize("unsafe", ["short", "has space here", "line\nbreak-123", "x" * 129])
def test_unsafe_incoming_id_is_replaced(unsafe: str) -> None:
    assert call(**{HEADER: unsafe})[HEADER] != unsafe


def test_id_is_cleared_after_the_request() -> None:
    call()

    assert current_request_id() is None


def test_middleware_is_installed(client: Client) -> None:
    assert client.get("/not-a-page").has_header(HEADER)


def test_id_is_cleared_when_the_view_fails() -> None:
    def failing_view(request: HttpRequest) -> HttpResponse:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        RequestIdMiddleware(failing_view)(RequestFactory().get("/"))

    assert current_request_id() is None
