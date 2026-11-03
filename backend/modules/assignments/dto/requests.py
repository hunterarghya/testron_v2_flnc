"""What the teacher sends (api_contract.md §2.6): `CreateAssignment`, `UpdateAssignment`, the
audience, the password and the list's filters."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.assignments.domain.assignment import Settings, SettingsPatch
from modules.assignments.domain.settings import Integrity, Publication
from modules.assignments.domain.values import PublicationMode, PublishContent, WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.services.commands.create_assignment import NewAssignment
from modules.assignments.services.queries.list_assignments import AssignmentFilter, Tab
from modules.authoring import public as authoring

MAX_AUDIENCE = 1000
MAX_GROUPS = 50
# Wide enough for any title; the domain cleans it and checks the real limit
Title = Annotated[str, Field(max_length=400)]
Password = Annotated[str, Field(max_length=64)]


class _In(Schema):
    model_config = ConfigDict(extra="forbid")


class ManualWindowIn(_In):
    kind: Literal["MANUAL"]
    planned_at: datetime | None = None
    late_entry_s: int | None = None


class ScheduledWindowIn(_In):
    kind: Literal["SCHEDULED"]
    starts_at: datetime
    late_entry_s: int | None = None


class DeadlineWindowIn(_In):
    kind: Literal["DEADLINE"]
    opens_at: datetime
    closes_at: datetime


class OpenWindowIn(_In):
    kind: Literal["OPEN"]


WindowIn = Annotated[
    ManualWindowIn | ScheduledWindowIn | DeadlineWindowIn | OpenWindowIn,
    Field(discriminator="kind"),
]


class TotalOverrideIn(_In):
    kind: Literal["TOTAL"]
    duration_s: int = Field(gt=0)


class SectionedOverrideIn(_In):
    kind: Literal["SECTIONED"]
    section_durations_s: dict[UUID, Annotated[int, Field(gt=0)]]


class PerQuestionOverrideIn(_In):
    kind: Literal["PER_QUESTION"]
    default_question_s: int = Field(gt=0)


TimingOverrideIn = Annotated[
    TotalOverrideIn | SectionedOverrideIn | PerQuestionOverrideIn, Field(discriminator="kind")
]


class GateIn(_In):
    requires_activation: bool
    password: Password | None = None
    password_confirm: Password | None = None


class GatePatchIn(_In):
    """The password has its own endpoint (D-07)."""

    requires_activation: bool


class AssignmentIntegrityIn(_In):
    grace_s: int
    max_warnings: int
    action: Literal["AUTO_SUBMIT", "DISQUALIFY"]

    def to_integrity(self) -> Integrity:
        return Integrity(self.grace_s, self.max_warnings, self.action)


class PublicationIn(_In):
    mode: PublicationMode
    delay_s: int | None = None
    content: PublishContent
    show_paper: bool
    show_solutions: bool
    show_rank_and_stats: bool

    def to_publication(self) -> Publication:
        return Publication(**self.model_dump())


class CreateAssignmentIn(_In):
    test_id: UUID
    title: Title
    student_ids: list[UUID] = Field(max_length=MAX_AUDIENCE)
    source_group_ids: list[UUID] = Field(default_factory=list, max_length=MAX_GROUPS)
    window: WindowIn
    gate: GateIn
    timing_override: TimingOverrideIn | None = None
    integrity: AssignmentIntegrityIn
    publication: PublicationIn

    def to_new(self) -> NewAssignment:
        return NewAssignment(
            test_id=self.test_id,
            settings=Settings(
                title=self.title,
                window=to_window(self.window),
                requires_activation=self.gate.requires_activation,
                integrity=self.integrity.to_integrity(),
                publication=self.publication.to_publication(),
            ),
            student_ids=self.student_ids,
            timing_override=None
            if self.timing_override is None
            else to_override(self.timing_override),
            password=self.gate.password,
            password_confirm=self.gate.password_confirm,
            source_group_ids=self.source_group_ids,
        )


class UpdateAssignmentIn(_In):
    title: Title | None = None
    window: WindowIn | None = None
    gate: GatePatchIn | None = None
    integrity: AssignmentIntegrityIn | None = None
    publication: PublicationIn | None = None

    def to_patch(self) -> SettingsPatch:
        return SettingsPatch(
            title=self.title,
            window=None if self.window is None else to_window(self.window),
            requires_activation=None if self.gate is None else self.gate.requires_activation,
            integrity=None if self.integrity is None else self.integrity.to_integrity(),
            publication=None if self.publication is None else self.publication.to_publication(),
        )


class AudienceIn(_In):
    student_ids: list[UUID] = Field(min_length=1, max_length=MAX_AUDIENCE)


class ReplaceAudienceIn(AudienceIn):
    # Leave out to keep the groups the audience was picked from (ADR-071)
    source_group_ids: list[UUID] | None = Field(default=None, max_length=MAX_GROUPS)


class PasswordIn(_In):
    """`{password, password_confirm}`, or `{password: null}` to remove it."""

    password: Password | None
    password_confirm: Password | None = None


class AssignmentFilterIn(_In):
    state: Tab | None = None
    group_id: UUID | None = None
    q: str | None = Field(default=None, max_length=100)
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None

    def to_filter(self) -> AssignmentFilter:
        return AssignmentFilter(
            tab=self.state, group_id=self.group_id, search=self.q, from_at=self.from_, to_at=self.to
        )


def to_window(window: WindowIn) -> Window:
    kind = WindowKind(window.kind)
    fields = window.model_dump(exclude={"kind"})
    return Window(kind, **fields)


def to_override(timing: TimingOverrideIn) -> authoring.TimingOverride:
    return authoring.TimingOverride(
        kind=authoring.TimingKind(timing.kind),
        **timing.model_dump(exclude={"kind"}),
    )
