"""list_assignments and get_assignment (T-06, T-08, api_contract.md §3.3)."""

from datetime import timedelta
from uuid import UUID

import pytest
from pytest_django import DjangoAssertNumQueries

from conftest import MakeCtx
from core.context import Actor, Ctx, Role
from core.errors import Forbidden, NotFound
from modules.assignments.domain.editing import BEFORE_START, PublicationState
from modules.assignments.domain.values import LifecycleState, WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.services.commands.cancel_assignment import cancel_assignment
from modules.assignments.services.commands.create_assignment import create_assignment
from modules.assignments.services.queries.get_assignment import get_assignment
from modules.assignments.services.queries.list_assignments import (
    AssignmentFilter,
    Tab,
    list_assignments,
)
from tests.factories.assignments import assignable_test, new_assignment
from tests.factories.identity import make_user
from tests.factories.students import make_group, make_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def assign(ctx: Ctx, title: str, students: list[UUID] | None = None, **changes: object) -> UUID:
    new = new_assignment(
        assignable_test().id, students or [make_student().id], title=title, **changes
    )
    return create_assignment(ctx, new=new).row.record.id


def titles(ctx: Ctx, filters: AssignmentFilter) -> list[str]:
    page = list_assignments(ctx, filters=filters, offset=0, limit=50)
    return [row.record.settings.title for row in page.rows]


def test_tabs_follow_the_derived_state(teacher_ctx: Ctx) -> None:
    soon = teacher_ctx.now + timedelta(hours=1)
    assign(teacher_ctx, "Open")
    assign(teacher_ctx, "Locked", window=Window(WindowKind.MANUAL))
    assign(teacher_ctx, "Later", window=Window(WindowKind.SCHEDULED, starts_at=soon))
    cancel_assignment(teacher_ctx, assignment_id=assign(teacher_ctx, "Off"))

    assert titles(teacher_ctx, AssignmentFilter(tab=Tab.UPCOMING)) == ["Later", "Locked"]
    assert titles(teacher_ctx, AssignmentFilter(tab=Tab.LIVE)) == ["Open"]
    assert titles(teacher_ctx, AssignmentFilter(tab=Tab.CANCELLED)) == ["Off"]
    assert titles(teacher_ctx, AssignmentFilter(tab=Tab.CLOSED)) == []
    assert len(titles(teacher_ctx, AssignmentFilter())) == 4


def test_search_group_and_dates_narrow_the_list(teacher_ctx: Ctx) -> None:
    member = make_student()
    group = make_group("11A", [member.id])
    soon = teacher_ctx.now + timedelta(days=3)
    assign(teacher_ctx, "Genetics", [member.id])
    assign(teacher_ctx, "Cell Biology", window=Window(WindowKind.SCHEDULED, starts_at=soon))

    assert titles(teacher_ctx, AssignmentFilter(search="gene")) == ["Genetics"]
    assert titles(teacher_ctx, AssignmentFilter(group_id=group.id)) == ["Genetics"]
    assert titles(teacher_ctx, AssignmentFilter(from_at=teacher_ctx.now + timedelta(days=1))) == [
        "Cell Biology"
    ]
    assert titles(teacher_ctx, AssignmentFilter(to_at=teacher_ctx.now + timedelta(days=1))) == [
        "Genetics"
    ]


def test_pages_and_totals(teacher_ctx: Ctx) -> None:
    for title in ("A", "B", "C"):
        assign(teacher_ctx, title)

    page = list_assignments(teacher_ctx, filters=AssignmentFilter(), offset=1, limit=1)

    assert ([row.record.settings.title for row in page.rows], page.total) == (["B"], 3)


def test_the_list_reads_a_fixed_number_of_queries(
    teacher_ctx: Ctx, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    for title in ("A", "B", "C", "D"):
        assign(teacher_ctx, title, [make_student().id, make_student().id])

    # assignments, audience counts, extensions
    with django_assert_num_queries(3):
        list_assignments(teacher_ctx, filters=AssignmentFilter(), offset=0, limit=50)


def test_the_overview_shows_state_audience_and_what_can_change(teacher_ctx: Ctx) -> None:
    student = make_student(name="Rina")
    assignment_id = assign(teacher_ctx, "Locked", [student.id], window=Window(WindowKind.MANUAL))

    detail = get_assignment(teacher_ctx, assignment_id=assignment_id)

    assert detail.row.state is LifecycleState.WAITING
    assert detail.row.publication_state is PublicationState.UNPUBLISHED
    assert (detail.row.audience_count, detail.row.locked) == (1, False)
    assert [(s.name, s.has_attempt) for s in detail.audience] == [("Rina", False)]
    assert detail.editable_fields == BEFORE_START
    assert detail.allow_return is False  # the test's default


def test_only_the_teacher_reads_and_missing_is_not_found(
    teacher_ctx: Ctx, make_ctx: MakeCtx
) -> None:
    student = make_student()
    assignment_id = assign(teacher_ctx, "Mine", [student.id])

    with pytest.raises(Forbidden):
        get_assignment(
            make_ctx(Actor(user_id=student.id, role=Role.STUDENT)), assignment_id=assignment_id
        )
    with pytest.raises(NotFound):
        get_assignment(teacher_ctx, assignment_id=student.id)
