from uuid import UUID

from modules.students.repositories import memberships


def list_group_member_ids(group_id: UUID) -> set[UUID]:
    """Everyone in the group, whatever their status: the assignment list's group filter
    (T-06). No policy here: callers are other modules' use cases."""
    return memberships.member_ids(group_id)
