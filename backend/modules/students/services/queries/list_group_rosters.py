from collections.abc import Sequence
from uuid import UUID

from modules.students.domain.values import GroupRoster
from modules.students.repositories import memberships


def list_group_rosters(group_ids: Sequence[UUID]) -> list[GroupRoster]:
    """These groups with their ACTIVE members, by name; unknown ids are left out. Two
    queries. No policy here: callers are other modules' use cases."""
    return memberships.rosters(list(dict.fromkeys(group_ids)))
