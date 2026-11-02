from datetime import datetime
from typing import Literal
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.students.domain.admission import BulkOutcome
from modules.students.domain.values import StudentRow

# The tabs of T-14; UNVERIFIED and ANONYMIZED accounts are never listed
ListedStatus = Literal["ACTIVE", "PENDING", "DECLINED", "DEACTIVATED"]
# Bulk actions stay small enough for one quick transaction
MAX_BULK = 500


class StudentFilterIn(Schema):
    """`?status=PENDING&q=rina`, next to the page parameters."""

    model_config = ConfigDict(extra="forbid")

    status: ListedStatus = "ACTIVE"
    q: str | None = Field(default=None, max_length=100)


class StudentIdsIn(Schema):
    model_config = ConfigDict(extra="forbid")

    student_ids: list[UUID] = Field(min_length=1, max_length=MAX_BULK)


class AnonymizeIn(Schema):
    model_config = ConfigDict(extra="forbid")

    confirm_name: str = Field(max_length=240)


class StudentRowOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    email: str
    status: ListedStatus
    joined_at: datetime
    requested_at: datetime | None
    decided_at: datetime | None
    deactivated_at: datetime | None
    performance_shared: bool

    @classmethod
    def from_row(cls, row: StudentRow) -> "StudentRowOut":
        return cls(
            id=row.id,
            name=row.name,
            email=row.email,
            status=row.status.value,  # type: ignore[arg-type]  # only listed statuses are queried
            joined_at=row.joined_at,
            requested_at=row.requested_at,
            decided_at=row.decided_at,
            deactivated_at=row.deactivated_at,
            performance_shared=row.performance_shared,
        )


class SkippedOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    reason: str


class BulkResultOut(Schema):
    """`{succeeded, skipped}`: a student in the wrong status is skipped, not an error."""

    model_config = ConfigDict(extra="forbid")

    succeeded: list[UUID]
    skipped: list[SkippedOut]

    @classmethod
    def from_outcome(cls, outcome: BulkOutcome) -> "BulkResultOut":
        return cls(
            succeeded=list(outcome.applied),
            skipped=[
                SkippedOut(id=skip.student_id, reason=skip.reason) for skip in outcome.skipped
            ],
        )
