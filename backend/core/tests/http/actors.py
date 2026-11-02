"""Test actors, and a resolver that reads the actor a test put on the request."""

from uuid import UUID

from django.http import HttpRequest

from core.context import ANONYMOUS, Actor, Role, StudentStatus

RESOLVER = "core.tests.http.actors.actor_from_request"
_META_KEY = "test.actor"

TEACHER = Actor(user_id=UUID(int=1), role=Role.TEACHER)
ACTIVE_STUDENT = Actor(UUID(int=2), Role.STUDENT, StudentStatus.ACTIVE)
PENDING_STUDENT = Actor(UUID(int=3), Role.STUDENT, StudentStatus.PENDING)
DEACTIVATED_STUDENT = Actor(UUID(int=4), Role.STUDENT, StudentStatus.DEACTIVATED)


def actor_from_request(request: HttpRequest) -> Actor:
    actor = request.META.get(_META_KEY, ANONYMOUS)
    assert isinstance(actor, Actor)
    return actor


def as_actor(request: HttpRequest, actor: Actor) -> HttpRequest:
    request.META[_META_KEY] = actor
    return request
