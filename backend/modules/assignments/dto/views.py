"""What the teacher sees (api_contract.md §3.3): `AssignmentRow` and `AssignmentDetail`."""

from datetime import datetime
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.assignments.domain.editing import PublicationState
from modules.assignments.domain.values import LifecycleState, WindowKind
from modules.assignments.services.views import AssignmentDetail, AssignmentRow, AudienceStudent


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class WindowSummaryOut(_Out):
    planned_at: datetime | None
    starts_at: datetime | None
    opens_at: datetime | None
    closes_at: datetime | None
    late_entry_s: int | None


class AudienceSummaryOut(_Out):
    count: int
    summary: str


class ProgressOut(_Out):
    ended: int
    in_progress: int
    audience: int


class AssignmentRowOut(_Out):
    id: UUID
    title: str
    test_id: UUID
    window_kind: WindowKind
    window_summary: WindowSummaryOut
    state: LifecycleState
    audience: AudienceSummaryOut
    progress: ProgressOut
    publication_state: PublicationState
    locked: bool

    @classmethod
    def from_row(cls, row: AssignmentRow) -> Self:
        record = row.record
        window = record.settings.window
        return cls(
            id=record.id,
            title=record.settings.title,
            test_id=record.test_id,
            window_kind=window.kind,
            window_summary=WindowSummaryOut(
                planned_at=window.planned_at,
                starts_at=window.starts_at,
                opens_at=window.opens_at,
                closes_at=window.closes_at,
                late_entry_s=window.late_entry_s,
            ),
            state=row.state,
            # Picked groups aren't stored, so the summary is the count (backlog B-18)
            audience=AudienceSummaryOut(
                count=row.audience_count, summary=f"{row.audience_count} students"
            ),
            progress=ProgressOut(
                ended=row.progress.ended,
                in_progress=row.progress.in_progress,
                audience=row.audience_count,
            ),
            publication_state=row.publication_state,
            locked=row.locked,
        )


class GateOut(_Out):
    requires_activation: bool
    has_password: bool


class TimingOut(_Out):
    kind: str
    total_duration_s: int
    allow_return: bool


class IntegrityOut(_Out):
    grace_s: int
    max_warnings: int
    action: str


class PublicationOut(_Out):
    mode: str
    delay_s: int | None
    content: str
    show_paper: bool
    show_solutions: bool
    show_rank_and_stats: bool
    published_at: datetime | None
    publish_at: datetime | None


class AudienceStudentOut(_Out):
    id: UUID
    name: str
    group_names: list[str]
    has_attempt: bool

    @classmethod
    def from_student(cls, student: AudienceStudent) -> Self:
        return cls(
            id=student.student_id,
            name=student.name,
            group_names=student.group_names,
            has_attempt=student.has_attempt,
        )


class AssignmentDetailOut(AssignmentRowOut):
    gate: GateOut
    timing: TimingOut
    integrity: IntegrityOut
    publication: PublicationOut
    activated_at: datetime | None
    ended_at: datetime | None
    ends_at: datetime | None
    audience_students: list[AudienceStudentOut]
    editable_fields: list[str]

    @classmethod
    def from_detail(cls, detail: AssignmentDetail) -> Self:
        record = detail.row.record
        settings, timeline = record.settings, record.timeline
        publication, integrity = settings.publication, settings.integrity
        return cls(
            **AssignmentRowOut.from_row(detail.row).model_dump(),
            gate=GateOut(
                requires_activation=settings.requires_activation,
                has_password=record.has_password,
            ),
            timing=TimingOut(
                kind=record.timing_kind,
                total_duration_s=timeline.total_duration_s,
                allow_return=detail.allow_return,
            ),
            integrity=IntegrityOut(
                grace_s=integrity.grace_s,
                max_warnings=integrity.max_warnings,
                action=integrity.action,
            ),
            publication=PublicationOut(
                mode=publication.mode.value,
                delay_s=publication.delay_s,
                content=publication.content.value,
                show_paper=publication.show_paper,
                show_solutions=publication.show_solutions,
                show_rank_and_stats=publication.show_rank_and_stats,
                published_at=record.published_at,
                publish_at=detail.publish_at,
            ),
            activated_at=timeline.activated_at,
            ended_at=timeline.ended_at,
            ends_at=detail.row.ends_at,
            audience_students=[AudienceStudentOut.from_student(s) for s in detail.audience],
            editable_fields=list(detail.editable_fields),
        )


class PasswordOut(_Out):
    password: str | None
