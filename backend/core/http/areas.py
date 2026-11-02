"""Router-level guards: the first of the two authorization gates (security.md §3.1).

Each guard is a Ninja `auth=` callable. It resolves the actor, refuses the wrong
kind of person, and hands the actor to the operation as `request.auth`. The use
case's own policy is the second gate and still runs.

Core can't import the identity module, so the function that turns a request into
an Actor is named by the `ACTOR_RESOLVER` setting (a dotted path).
"""

from collections.abc import Callable
from functools import cache

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

from core.context import ANONYMOUS, Actor
from core.errors import AccountNotActive, Forbidden, NotAuthenticated

ActorResolver = Callable[[HttpRequest], Actor]


def anonymous_actor(request: HttpRequest) -> Actor:
    """The resolver used until sessions exist: nobody is logged in."""
    return ANONYMOUS


def resolve_actor(request: HttpRequest) -> Actor:
    return _resolver(settings.ACTOR_RESOLVER)(request)


class SignedInArea:
    """Any logged-in person, whatever their role or status (`/auth/logout`, `/auth/profile`)."""

    def __call__(self, request: HttpRequest) -> Actor:
        return _signed_in(request)


class TeacherArea:
    """`/admin/**`: the teacher only."""

    def __call__(self, request: HttpRequest) -> Actor:
        actor = _signed_in(request)
        if not actor.is_teacher:
            raise Forbidden()
        return actor


class StudentArea:
    """`/my/**` and `/attempts/**`: ACTIVE students only."""

    def __call__(self, request: HttpRequest) -> Actor:
        actor = _signed_in(request)
        if actor.is_teacher:
            raise Forbidden()
        if not actor.is_active_student:
            raise AccountNotActive(context={"status": actor.student_status})
        return actor


def _signed_in(request: HttpRequest) -> Actor:
    actor = resolve_actor(request)
    if not actor.is_authenticated:
        raise NotAuthenticated()
    return actor


@cache
def _resolver(path: str) -> ActorResolver:
    resolver: ActorResolver = import_string(path)
    return resolver
