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
from tests.factories.authoring import make_numerical, make_question, make_section, make_test
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


def exam_test(**test_fields: object) -> Test:
    """Two MCQs (option 1 correct, +4/-1) and a numerical question (answer 46), in that order,
    with no shuffling."""
    test = make_test(shuffle_questions=False, shuffle_options=False, **test_fields)
    section = make_section(test)
    make_question(section, 0)
    make_question(section, 1)
    make_numerical(section, 2, answer="46")
    return test


def sectioned_test(*, allow_return: bool, durations: tuple[int, ...] = (600, 1200)) -> Test:
    """One MCQ per section, each section timed (P-04)."""
    test = make_test(timing_kind="SECTIONED", duration_s=None, allow_return=allow_return)
    for position, duration in enumerate(durations):
        make_question(make_section(test, position, title=f"S{position + 1}", duration_s=duration))
    return test


def rapid_test(questions: int = 3, seconds: int = 30) -> Test:
    """Rapid fire (P-05): one timed stage per question."""
    test = make_test(timing_kind="PER_QUESTION", duration_s=None, default_question_s=seconds)
    section = make_section(test)
    for position in range(questions):
        make_question(section, position)
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


def assign(
    student_ids: Sequence[UUID], *, now: datetime, test: Test | None = None, **changes: Any
) -> UUID:
    """An assignment made by a new teacher at `now`, through the real use case."""
    ctx = teacher_ctx(now)
    new = new_assignment((test or assignable_test()).id, student_ids, **changes)
    return create_assignment(ctx, new=new).row.record.id


def start(assignment_id: UUID, *, now: datetime) -> None:
    activate_assignment(teacher_ctx(now), assignment_id=assignment_id)


def last_seen(assignment_id: UUID, student_id: UUID) -> datetime | None:
    row = LobbyPresence.objects.filter(assignment_id=assignment_id, student_id=student_id).first()
    return None if row is None else row.last_seen_at


def teacher_ctx(now: datetime) -> Ctx:
    # There is one teacher account; a test may have made it already
    teacher = User.objects.filter(role=Role.TEACHER).first() or make_user(teacher=True)
    return Ctx(Actor(user_id=teacher.id, role=Role.TEACHER), now=now, request_id="factory")
