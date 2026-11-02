from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.students.domain.bulk import BulkOutcome
from modules.students.domain.groups import plan_unsharing
from modules.students.policies import ensure_teacher
from modules.students.repositories import performance_shares, students


def unshare_performance(ctx: Ctx, *, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Stop showing students their performance; off is the default (§3.2 PerformanceShare #1)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        statuses = students.lock_statuses_for_update(student_ids)
        outcome = plan_unsharing(student_ids, statuses, performance_shares.shared_ids(student_ids))
        performance_shares.unshare(outcome.applied)
    return outcome
