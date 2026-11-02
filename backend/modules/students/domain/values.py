from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.context import StudentStatus


@dataclass(frozen=True, slots=True)
class StudentRow:
    """One line of the teacher's Students table (T-14)."""

    id: UUID
    name: str
    email: str
    status: StudentStatus
    joined_at: datetime
    requested_at: datetime | None
    decided_at: datetime | None
    deactivated_at: datetime | None
    performance_shared: bool
