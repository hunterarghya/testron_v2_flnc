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
    group_names: list[str]


@dataclass(frozen=True, slots=True)
class GroupSummary:
    """A group as T-16 lists it."""

    id: UUID
    name: str
    description: str
    archived_at: datetime | None
    member_count: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class GroupMember:
    """One student on T-17's Students tab."""

    id: UUID
    name: str
    email: str
    status: StudentStatus
    added_at: datetime
    performance_shared: bool


@dataclass(frozen=True, slots=True)
class AudienceCandidate:
    """An ACTIVE student the assignment wizard would add for the chosen groups (T-07)."""

    student_id: UUID
    name: str
    email: str
    group_names: list[str]


@dataclass(frozen=True, slots=True)
class GroupRef:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class StudentDetail:
    """T-15's header: the student's row plus their active groups, with ids to act on."""

    row: StudentRow
    groups: list[GroupRef]
