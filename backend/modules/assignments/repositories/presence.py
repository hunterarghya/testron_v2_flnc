from datetime import datetime
from uuid import UUID

from modules.assignments.models import LobbyPresence


def touch(assignment_id: UUID, student_id: UUID, *, now: datetime) -> None:
    """One row per student, moved forward on each gate poll (T-09). One upsert, so two polls
    at once can't collide."""
    LobbyPresence.objects.bulk_create(
        [LobbyPresence(assignment_id=assignment_id, student_id=student_id, last_seen_at=now)],
        update_conflicts=True,
        unique_fields=["assignment", "student"],
        update_fields=["last_seen_at"],
    )


def last_seen(assignment_id: UUID) -> dict[UUID, datetime]:
    rows = LobbyPresence.objects.filter(assignment_id=assignment_id).values_list(
        "student_id", "last_seen_at"
    )
    return dict(rows)
