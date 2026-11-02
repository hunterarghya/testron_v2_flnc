from uuid import UUID

import pytest

from core.context import StudentStatus as S
from modules.students.domain.bulk import NOT_FOUND, Skip
from modules.students.domain.groups import (
    normalize_group_name,
    plan_adding_members,
    plan_removing_members,
    plan_sharing,
    plan_unsharing,
)

A, B, C, D, MISSING = (UUID(int=n) for n in (1, 2, 3, 4, 99))


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("Class 11 A", "class 11 a"),
        ("  class   11  A ", "class 11 a"),
        ("CLASS 11 A", "class 11 a"),
        ("একাদশ ক", "একাদশ ক"),
        ("Straße", "strasse"),
    ],
)
def test_group_names_compare_ignoring_case_and_spaces(raw: str, normalized: str) -> None:
    assert normalize_group_name(raw) == normalized


def test_only_admitted_students_join_and_members_are_skipped() -> None:
    statuses = {A: S.ACTIVE, B: S.DEACTIVATED, C: S.PENDING, D: S.ACTIVE}

    outcome = plan_adding_members([A, B, C, D, MISSING], statuses, members={D})

    assert outcome.applied == (A, B)
    assert outcome.skipped == (
        Skip(C, "status_pending"),
        Skip(D, "already_member"),
        Skip(MISSING, NOT_FOUND),
    )


def test_removing_skips_non_members() -> None:
    outcome = plan_removing_members([A, B], {A: S.ACTIVE, B: S.ACTIVE}, members={A})

    assert outcome.applied == (A,)
    assert outcome.skipped == (Skip(B, "not_member"),)


def test_sharing_with_admitted_students_once() -> None:
    statuses = {A: S.ACTIVE, B: S.DECLINED, C: S.ACTIVE}

    outcome = plan_sharing([A, B, C], statuses, shared={C})

    assert outcome.applied == (A,)
    assert outcome.skipped == (Skip(B, "status_declined"), Skip(C, "already_shared"))


def test_unsharing_skips_students_not_shared() -> None:
    outcome = plan_unsharing([A, B], {A: S.ACTIVE, B: S.ACTIVE}, shared={B})

    assert outcome.applied == (B,)
    assert outcome.skipped == (Skip(A, "not_shared"),)
