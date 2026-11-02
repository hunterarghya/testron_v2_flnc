from uuid import UUID

import pytest

from core.context import StudentStatus as S
from modules.students.domain.admission import (
    NOT_FOUND,
    AdmissionAction,
    Skip,
    can_apply,
    plan_bulk,
    status_after,
    status_after_email_verified,
)
from modules.students.domain.errors import AdmissionStepNotAllowed

A = AdmissionAction
ALLOWED = {
    A.APPROVE: {S.PENDING},
    A.DECLINE: {S.PENDING},
    A.DEACTIVATE: {S.ACTIVE},
    A.REACTIVATE: {S.DEACTIVATED},
    A.ANONYMIZE: {S.ACTIVE, S.DEACTIVATED},
}


@pytest.mark.parametrize("action", list(A))
@pytest.mark.parametrize("status", list(S))
def test_each_action_starts_only_from_its_statuses(action: A, status: S) -> None:
    # domain_model.md §7.1, every cell of the action-by-status table
    assert can_apply(action, status) is (status in ALLOWED[action])


@pytest.mark.parametrize(
    ("action", "after"),
    [
        (A.APPROVE, S.ACTIVE),
        (A.DECLINE, S.DECLINED),
        (A.DEACTIVATE, S.DEACTIVATED),
        (A.REACTIVATE, S.ACTIVE),
        (A.ANONYMIZE, S.ANONYMIZED),
    ],
)
def test_each_action_leads_to_one_status(action: A, after: S) -> None:
    assert status_after(action) is after


def test_v1_f30_declined_is_final() -> None:
    assert not any(can_apply(action, S.DECLINED) for action in A)


ONE, TWO, THREE, MISSING = (UUID(int=n) for n in (1, 2, 3, 99))


def test_bulk_applies_to_the_right_students_and_skips_the_rest() -> None:
    outcome = plan_bulk(
        A.APPROVE, [ONE, TWO, MISSING, THREE], {ONE: S.PENDING, TWO: S.ACTIVE, THREE: S.PENDING}
    )

    assert outcome.applied == (ONE, THREE)
    assert outcome.skipped == (Skip(TWO, "status_active"), Skip(MISSING, NOT_FOUND))


def test_bulk_counts_a_repeated_id_once() -> None:
    outcome = plan_bulk(A.DEACTIVATE, [ONE, ONE, ONE], {ONE: S.ACTIVE})

    assert outcome.applied == (ONE,)
    assert outcome.skipped == ()


def test_bulk_with_nothing_to_do_changes_nothing() -> None:
    outcome = plan_bulk(A.REACTIVATE, [ONE], {ONE: S.ACTIVE})

    assert outcome.applied == ()


def test_verified_email_makes_a_join_request() -> None:
    assert status_after_email_verified(S.UNVERIFIED) is S.PENDING


@pytest.mark.parametrize("status", [status for status in S if status is not S.UNVERIFIED])
def test_only_unverified_accounts_can_be_verified(status: S) -> None:
    with pytest.raises(AdmissionStepNotAllowed):
        status_after_email_verified(status)
