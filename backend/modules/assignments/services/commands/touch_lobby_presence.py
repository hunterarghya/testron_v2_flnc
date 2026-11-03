from datetime import datetime
from uuid import UUID

from modules.assignments.repositories import presence


def touch_lobby_presence(assignment_id: UUID, student_id: UUID, *, now: datetime) -> None:
    """The student has the gate open: "Joined" in the teacher's lobby for the next 30 s
    (T-09). No policy here: the caller is delivery's gate, after its audience check."""
    presence.touch(assignment_id, student_id, now=now)
