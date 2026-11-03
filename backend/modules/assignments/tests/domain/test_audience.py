"""The audience rules (domain_model.md §3.5 #1, #3; E-11, E-35)."""

from uuid import UUID, uuid4

import pytest

from core.bulk import NOT_FOUND, Skip
from core.context import StudentStatus as S
from core.errors import FieldsInvalid
from modules.assignments.domain.audience import (
    ALREADY_MEMBER,
    NOT_MEMBER,
    ensure_all_active,
    ensure_audience_not_empty,
    plan_additions,
    plan_removals,
)
from modules.assignments.domain.errors import AudienceMemberHasAttempt

A, B, C, D = (uuid4() for _ in range(4))


def test_an_audience_needs_someone() -> None:
    with pytest.raises(FieldsInvalid):
        ensure_audience_not_empty([])
    ensure_audience_not_empty([A])


def test_a_new_audience_is_active_students_each_once() -> None:
    assert ensure_all_active([A, B, A], {A: S.ACTIVE, B: S.ACTIVE}) == [A, B]


@pytest.mark.parametrize("statuses", [{A: S.ACTIVE}, {A: S.ACTIVE, B: S.DEACTIVATED}])
def test_a_new_audience_refuses_anyone_else(statuses: dict[UUID, S]) -> None:
    with pytest.raises(FieldsInvalid):
        ensure_all_active([A, B], statuses)


def test_additions_skip_unknown_inactive_and_present_students() -> None:
    outcome = plan_additions([A, B, C, D, A], {A: S.ACTIVE, B: S.PENDING, C: S.ACTIVE}, {C})

    assert outcome.applied == (A,)
    assert outcome.skipped == (
        Skip(B, "status_pending"),
        Skip(C, ALREADY_MEMBER),
        Skip(D, NOT_FOUND),
    )


def test_removals_skip_non_members() -> None:
    outcome = plan_removals([A, B, A], members={A}, with_attempt=set())

    assert outcome.applied == (A,)
    assert outcome.skipped == (Skip(B, NOT_MEMBER),)


def test_a_student_who_began_stays_and_nobody_is_removed() -> None:
    with pytest.raises(AudienceMemberHasAttempt) as raised:
        plan_removals([A, B], members={A, B}, with_attempt={B})

    assert raised.value.context == {"student_ids": [str(B)]}
