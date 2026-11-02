from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx
from modules.students.domain.values import GroupMember, GroupSummary
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups, memberships


@dataclass(frozen=True, slots=True)
class GroupDetail:
    group: GroupSummary
    members: list[GroupMember]


def get_group(ctx: Ctx, *, group_id: UUID) -> GroupDetail:
    """One group with its members (T-17). Its assignments and performance join in later
    phases. Archived groups can still be opened."""
    ensure_teacher(ctx.actor)
    return GroupDetail(
        group=groups.get_group_summary(group_id), members=memberships.list_members(group_id)
    )
