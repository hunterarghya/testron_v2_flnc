"""A test that can be assigned, and the wizard's answers for it (not the use cases' rules)."""

from collections.abc import Sequence
from dataclasses import fields, replace
from datetime import datetime
from typing import Any
from uuid import UUID

from core.context import Actor, Ctx, Role
from modules.assignments.domain.assignment import Settings
from modules.assignments.domain.settings import Integrity, Publication
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.models import LobbyPresence
from modules.assignments.services.commands.activate_assignment import activate_assignment
from modules.assignments.services.commands.create_assignment import NewAssignment, create_assignment
from modules.authoring.models import Test
from tests.factories.authoring import make_question, make_section, make_test
from tests.factories.identity import User, make_user

SETTINGS = Settings(
    title="Cell Biology",
    window=Window(WindowKind.OPEN),
    requires_activation=False,
    integrity=Integrity(grace_s=5, max_warnings=3, action="AUTO_SUBMIT"),
    publication=Publication(),
)
_SETTING_NAMES = {field.name for field in fields(Settings)}


def assignable_test(**test_fields: object) -> Test:
    """A one-question test with no problems."""
    test = make_test(**test_fields)
    make_question(make_section(test))
    return test


def new_assignment(test_id: UUID, student_ids: Sequence[UUID], **changes: Any) -> NewAssignment:
    """`changes` may set Settings fields (title, window, …) or NewAssignment ones (password, …)."""
    settings = replace(SETTINGS, **{k: v for k, v in changes.items() if k in _SETTING_NAMES})
    rest = {k: v for k, v in changes.items() if k not in _SETTING_NAMES}
    return NewAssignment(test_id=test_id, settings=settings, student_ids=student_ids, **rest)


def locked(late_entry_s: int | None = None) -> Window:
    return Window(WindowKind.MANUAL, late_entry_s=late_entry_s)


def scheduled(starts_at: datetime) -> Window:
    return Window(WindowKind.SCHEDULED, starts_at=starts_at)


def assign(student_ids: Sequence[UUID], *, now: datetime, **changes: Any) -> UUID:
    """An assignment made by a new teacher at `now`, through the real use case."""
    ctx = _teacher_ctx(now)
    new = new_assignment(assignable_test().id, student_ids, **changes)
    return create_assignment(ctx, new=new).row.record.id


def start(assignment_id: UUID, *, now: datetime) -> None:
    activate_assignment(_teacher_ctx(now), assignment_id=assignment_id)


def last_seen(assignment_id: UUID, student_id: UUID) -> datetime | None:
    row = LobbyPresence.objects.filter(assignment_id=assignment_id, student_id=student_id).first()
    return None if row is None else row.last_seen_at


def _teacher_ctx(now: datetime) -> Ctx:
    # There is one teacher account; a test may have made it already
    teacher = User.objects.filter(role=Role.TEACHER).first() or make_user(teacher=True)
    return Ctx(Actor(user_id=teacher.id, role=Role.TEACHER), now=now, request_id="factory")
