from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.students.domain.values import GroupSummary
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups


def restore_group(ctx: Ctx, *, group_id: UUID) -> GroupSummary:
    """Bring an archived group back. Refused as `taken` if an active group has its name now."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        if groups.get_group_for_update(group_id).archived_at is not None:
            groups.set_archived_at(group_id, None, now=ctx.now)
    return groups.get_group_summary(group_id)
