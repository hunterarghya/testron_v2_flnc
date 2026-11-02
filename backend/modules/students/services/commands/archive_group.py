from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.students.domain.values import GroupSummary
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups


def archive_group(ctx: Ctx, *, group_id: UUID) -> GroupSummary:
    """Hide a group from pickers; its members, assignments and history stay (§3.2 #2, B-1).
    Archiving an archived group changes nothing."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        if groups.get_group_for_update(group_id).archived_at is None:
            groups.set_archived_at(group_id, ctx.now, now=ctx.now)
    return groups.get_group_summary(group_id)
