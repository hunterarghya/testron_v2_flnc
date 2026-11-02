from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.text import clean_text_line
from modules.students.domain.groups import normalize_group_name
from modules.students.domain.values import GroupSummary
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups


def update_group(
    ctx: Ctx, *, group_id: UUID, name: str | None, description: str | None
) -> GroupSummary:
    """Rename a group or change its description (T-17); fields left out stay as they are.
    The new name must still be unique among active groups."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        group = groups.get_group_for_update(group_id)
        new_name = name if name is not None else group.name
        new_description = clean_text_line(description) if description is not None else None
        groups.update_group(
            group_id,
            name=new_name,
            normalized_name=normalize_group_name(new_name),
            description=new_description if new_description is not None else group.description,
            now=ctx.now,
        )
    return groups.get_group_summary(group_id)
