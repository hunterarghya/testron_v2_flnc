from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.bulk import BulkOutcome
from core.context import Ctx
from modules.students.domain.groups import plan_adding_members
from modules.students.policies import ensure_teacher
from modules.students.repositories import memberships, students
from modules.students.services.group_access import lock_active_group


def add_group_members(ctx: Ctx, *, group_id: UUID, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Put students in a group (T-17, T-14 bulk). Only admitted students can join; existing
    members and others are skipped (domain_model.md §3.2 #1). Membership never grants access
    to a test by itself (§3.2 #3)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        lock_active_group(group_id)
        statuses = students.lock_statuses_for_update(student_ids)
        outcome = plan_adding_members(student_ids, statuses, memberships.member_ids(group_id))
        memberships.add_members(group_id, outcome.applied, now=ctx.now)
    return outcome
