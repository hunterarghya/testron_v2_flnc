from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.bulk import BulkOutcome
from core.context import Ctx
from core.errors import Invalid
from modules.students.domain.groups import plan_sharing
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups, memberships, performance_shares, students


def share_performance(
    ctx: Ctx, *, student_ids: Sequence[UUID] | None, group_id: UUID | None
) -> BulkOutcome:
    """Let students see their own chapter and topic performance (domain_model.md §3.2, D-06).

    Exactly one of `student_ids` or `group_id`. A group shares with its **current** members
    only; students who join later aren't shared automatically (§3.2 PerformanceShare #2).
    Already-shared students are skipped.
    """
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        targets = _targets(student_ids, group_id)
        statuses = students.lock_statuses_for_update(targets)
        outcome = plan_sharing(targets, statuses, performance_shares.shared_ids(targets))
        performance_shares.share(outcome.applied, now=ctx.now)
    return outcome


def _targets(student_ids: Sequence[UUID] | None, group_id: UUID | None) -> list[UUID]:
    if student_ids is not None and group_id is None:
        return list(student_ids)
    if group_id is not None and student_ids is None:
        groups.get_group_for_update(group_id)
        return sorted(memberships.member_ids(group_id))
    raise Invalid("Give either students or one group")
