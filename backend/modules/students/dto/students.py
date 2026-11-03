from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field, model_validator

from modules.students.domain.values import GroupRef, StudentDetail, StudentRow

# The tabs of T-14; UNVERIFIED and ANONYMIZED accounts are never listed
ListedStatus = Literal["ACTIVE", "PENDING", "DECLINED", "DEACTIVATED"]
# Bulk actions stay small enough for one quick transaction
MAX_BULK = 500


class StudentFilterIn(Schema):
    """`?status=PENDING&q=rina`, next to the page parameters."""

    model_config = ConfigDict(extra="forbid")

    status: ListedStatus = "ACTIVE"
    q: str | None = Field(default=None, max_length=100)
    group_id: UUID | None = None


class StudentIdsIn(Schema):
    model_config = ConfigDict(extra="forbid")

    student_ids: list[UUID] = Field(min_length=1, max_length=MAX_BULK)


class ApproveIn(Schema):
    model_config = ConfigDict(extra="forbid")

    student_ids: list[UUID] = Field(min_length=1, max_length=MAX_BULK)
    # Approved students join these groups too (T-14 Pending, "Add to group")
    group_ids: list[UUID] = Field(default_factory=list, max_length=20)


class ShareIn(Schema):
    """Exactly one: the ticked students, or every current member of one group (D-06)."""

    model_config = ConfigDict(extra="forbid")

    student_ids: list[UUID] | None = Field(default=None, min_length=1, max_length=MAX_BULK)
    group_id: UUID | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.student_ids is None) == (self.group_id is None):
            raise ValueError("Give either student_ids or group_id")
        return self


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
    group_names: list[str]

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
            group_names=row.group_names,
        )


class GroupRefOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str

    @classmethod
    def from_ref(cls, group: GroupRef) -> Self:
        return cls(id=group.id, name=group.name)


class StudentDetailOut(Schema):
    """T-15's header. `groups` are the student's active groups, with ids to add or remove."""

    model_config = ConfigDict(extra="forbid")

    student: StudentRowOut
    groups: list[GroupRefOut]

    @classmethod
    def from_detail(cls, detail: StudentDetail) -> Self:
        return cls(
            student=StudentRowOut.from_row(detail.row),
            groups=[GroupRefOut.from_ref(group) for group in detail.groups],
        )
