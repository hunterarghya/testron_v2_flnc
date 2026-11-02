from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.students.domain.bulk import BulkOutcome
from modules.students.domain.groups import plan_removing_members
from modules.students.policies import ensure_teacher
from modules.students.repositories import memberships, students
from modules.students.services.group_access import lock_active_group


def remove_group_members(ctx: Ctx, *, group_id: UUID, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Take students out of a group (T-17). Their results and past assignments are untouched:
    an assignment's audience was copied when it was made (ADR-016)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        lock_active_group(group_id)
        statuses = students.lock_statuses_for_update(student_ids)
        outcome = plan_removing_members(student_ids, statuses, memberships.member_ids(group_id))
        memberships.remove_members(group_id, outcome.applied)
    return outcome
