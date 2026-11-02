"""The one path every bulk admission action takes (approve, decline, deactivate, reactivate).

The teacher ticks several students; each is changed or skipped on their own, in one
transaction, with the rows locked so two clicks can't apply an action twice
(domain_model.md §3.2 #4). The login flag follows the status (database_schema.md §5.3).
"""

from collections.abc import Callable, Sequence
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.identity import public as identity
from modules.students.domain.admission import AdmissionAction, plan_bulk
from modules.students.domain.bulk import BulkOutcome
from modules.students.policies import ensure_teacher
from modules.students.repositories import students


def change_admission(ctx: Ctx, action: AdmissionAction, student_ids: Sequence[UUID]) -> BulkOutcome:
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        statuses = students.lock_statuses_for_update(student_ids)
        outcome = plan_bulk(action, student_ids, statuses)
        if outcome.applied:
            _EFFECTS[action](ctx, outcome.applied)
    return outcome


def _approve(ctx: Ctx, ids: Sequence[UUID]) -> None:
    students.mark_approved(ids, now=ctx.now)
    identity.set_accounts_active(ctx, user_ids=ids, active=True)


def _decline(ctx: Ctx, ids: Sequence[UUID]) -> None:
    # Still logged in, so they can read "Request declined" (screens S-05)
    students.mark_declined(ids, now=ctx.now)


def _deactivate(ctx: Ctx, ids: Sequence[UUID]) -> None:
    students.mark_deactivated(ids, now=ctx.now)
    identity.set_accounts_active(ctx, user_ids=ids, active=False)
    identity.end_sessions(user_ids=ids)


def _reactivate(ctx: Ctx, ids: Sequence[UUID]) -> None:
    students.mark_reactivated(ids, now=ctx.now)
    identity.set_accounts_active(ctx, user_ids=ids, active=True)


_Effect = Callable[[Ctx, Sequence[UUID]], None]
_EFFECTS: dict[AdmissionAction, _Effect] = {
    AdmissionAction.APPROVE: _approve,
    AdmissionAction.DECLINE: _decline,
    AdmissionAction.DEACTIVATE: _deactivate,
    AdmissionAction.REACTIVATE: _reactivate,
}
