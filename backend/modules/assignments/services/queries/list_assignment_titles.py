from collections.abc import Collection
from uuid import UUID

from modules.assignments.repositories import assignments


def list_assignment_titles(assignment_ids: Collection[UUID]) -> dict[UUID, str]:
    """Titles for labels (performance trends). No policy: callers are results' use cases,
    which check who may see the attempts first."""
    return assignments.titles(assignment_ids)
