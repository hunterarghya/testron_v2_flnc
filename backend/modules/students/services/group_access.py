"""Shared steps of the group use cases."""

from uuid import UUID

from modules.students.domain.errors import GroupArchived
from modules.students.models import Group
from modules.students.repositories import groups


def lock_active_group(group_id: UUID) -> Group:
    """The group, locked for this transaction; an archived group can't change (§3.2 #2)."""
    group = groups.get_group_for_update(group_id)
    if group.archived_at is not None:
        raise GroupArchived(context={"group_id": str(group_id)})
    return group
