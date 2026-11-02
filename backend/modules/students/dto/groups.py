from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import AfterValidator, BeforeValidator, ConfigDict, Field, StringConstraints

from core.text import clean_text_line
from modules.students.domain.values import AudienceCandidate, GroupMember, GroupSummary
from modules.students.models.group import MAX_GROUP_DESCRIPTION_LENGTH, MAX_GROUP_NAME_LENGTH
from modules.students.services.queries.get_group import GroupDetail


def _clean_group_name(raw: str) -> str:
    name = clean_text_line(raw)
    if not name:
        raise ValueError("Enter a name")
    if len(name) > MAX_GROUP_NAME_LENGTH:
        raise ValueError(f"Use at most {MAX_GROUP_NAME_LENGTH} characters")
    return name


def _split_ids(raw: object) -> object:
    # The contract's `?group_ids=a,b`; Ninja hands query lists over as ["a,b"]
    values = [raw] if isinstance(raw, str) else raw
    if not isinstance(values, list):
        return raw
    return [part.strip() for value in values for part in str(value).split(",") if part.strip()]


GroupName = Annotated[
    str, StringConstraints(max_length=MAX_GROUP_NAME_LENGTH * 2), AfterValidator(_clean_group_name)
]
Description = Annotated[str, StringConstraints(max_length=MAX_GROUP_DESCRIPTION_LENGTH)]


class GroupIn(Schema):
    model_config = ConfigDict(extra="forbid")

    name: GroupName
    description: Description = ""


class GroupPatchIn(Schema):
    model_config = ConfigDict(extra="forbid")

    name: GroupName | None = None
    description: Description | None = None


class GroupFilterIn(Schema):
    model_config = ConfigDict(extra="forbid")

    archived: bool = False
    q: str | None = Field(default=None, max_length=100)


class AudiencePreviewIn(Schema):
    model_config = ConfigDict(extra="forbid")

    group_ids: Annotated[list[UUID], BeforeValidator(_split_ids)] = Field(max_length=50)


class GroupOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    description: str
    archived_at: datetime | None
    member_count: int
    created_at: datetime

    @classmethod
    def from_summary(cls, group: GroupSummary) -> Self:
        return cls(
            id=group.id,
            name=group.name,
            description=group.description,
            archived_at=group.archived_at,
            member_count=group.member_count,
            created_at=group.created_at,
        )


class GroupMemberOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    email: str
    status: Literal["ACTIVE", "DEACTIVATED"]
    added_at: datetime
    performance_shared: bool

    @classmethod
    def from_member(cls, member: GroupMember) -> Self:
        return cls(
            id=member.id,
            name=member.name,
            email=member.email,
            status=member.status.value,  # type: ignore[arg-type]  # only admitted students are members
            added_at=member.added_at,
            performance_shared=member.performance_shared,
        )


class GroupDetailOut(Schema):
    model_config = ConfigDict(extra="forbid")

    group: GroupOut
    members: list[GroupMemberOut]

    @classmethod
    def from_detail(cls, detail: GroupDetail) -> Self:
        return cls(
            group=GroupOut.from_summary(detail.group),
            members=[GroupMemberOut.from_member(member) for member in detail.members],
        )


class AudienceCandidateOut(Schema):
    model_config = ConfigDict(extra="forbid")

    student_id: UUID
    name: str
    email: str
    group_names: list[str]

    @classmethod
    def from_candidate(cls, candidate: AudienceCandidate) -> Self:
        return cls(
            student_id=candidate.student_id,
            name=candidate.name,
            email=candidate.email,
            group_names=candidate.group_names,
        )
