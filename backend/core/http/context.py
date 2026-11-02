"""Build the use-case context from an HTTP request."""

from django.http import HttpRequest

from core.clock import get_clock
from core.context import Actor, Ctx
from core.http.areas import resolve_actor
from core.request_id import current_or_new_request_id


def ctx_from(request: HttpRequest) -> Ctx:
    """The actor (already resolved by the area guard, if there was one), now, and the request id."""
    return Ctx(
        actor=_actor_of(request),
        now=get_clock().now(),
        request_id=current_or_new_request_id(),
    )


def _actor_of(request: HttpRequest) -> Actor:
    # Public routes have no guard, but a logged-in caller is still known
    guarded = getattr(request, "auth", None)
    return guarded if isinstance(guarded, Actor) else resolve_actor(request)
