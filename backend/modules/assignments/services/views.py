"""What the teacher sees of an assignment (api_contract.md §3.3): a list row, or the whole
overview. Every use case that returns an assignment builds it here."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.assignments.domain.assignment import AssignmentRecord, Progress
from modules.assignments.domain.audience import PickedGroup, audience_summary
from modules.assignments.domain.editing import (
    PublicationState,
    editable_fields,
    publication_state,
    publish_at,
)
from modules.assignments.domain.entry import is_locked
from modules.assignments.domain.lifecycle import (
    ExtensionGrant,
    assignment_end,
    has_started,
    lifecycle_state,
)
from modules.assignments.domain.values import LifecycleState
from modules.assignments.repositories import attempt_facts, audience, extensions, papers
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class AssignmentRow:
    record: AssignmentRecord
    state: LifecycleState
    ends_at: datetime | None
    audience_count: int
    audience_summary: str
    progress: Progress
    publication_state: PublicationState
    # Students wait for Start or need a password
    locked: bool


@dataclass(frozen=True, slots=True)
class AudienceStudent:
    student_id: UUID
    name: str
    group_names: list[str]
    has_attempt: bool


@dataclass(frozen=True, slots=True)
class AssignmentDetail:
    row: AssignmentRow
    allow_return: bool
    publish_at: datetime | None
    audience: list[AudienceStudent]
    editable_fields: tuple[str, ...]


def assignment_rows(records: Sequence[AssignmentRecord], *, now: datetime) -> list[AssignmentRow]:
    """Three queries, however many assignments there are; two more if any used groups."""
    ids = [record.id for record in records]
    members = audience.members_by_assignment(ids)
    grants = extensions.grants_by_assignment(ids)
    progress = attempt_facts.progress_by_assignment(ids)
    groups = _picked_groups(records)
    return [
        _row(
            record,
            grants.get(record.id, []),
            progress[record.id],
            audience_summary(
                [groups[g] for g in record.source_group_ids if g in groups], members[record.id]
            ),
            len(members[record.id]),
            now,
        )
        for record in records
    ]


def assignment_detail(record: AssignmentRecord, *, now: datetime) -> AssignmentDetail:
    row = assignment_rows([record], now=now)[0]
    with_attempt = attempt_facts.students_with_attempts(record.id)
    people = students.describe_students(audience.member_ids(record.id))
    return AssignmentDetail(
        row=row,
        allow_return=papers.allow_return(record.id),
        publish_at=publish_at(record.settings.publication, row.ends_at),
        audience=[
            AudienceStudent(p.student_id, p.name, p.group_names, p.student_id in with_attempt)
            for p in people
        ],
        editable_fields=editable_fields(
            cancelled=row.state is LifecycleState.CANCELLED,
            started=has_started(row.state, record.timeline),
        ),
    )


def is_started(record: AssignmentRecord, *, now: datetime) -> bool:
    grants = extensions.grants_by_assignment([record.id]).get(record.id, [])
    progress = attempt_facts.progress_by_assignment([record.id])[record.id]
    return has_started(_state(record, grants, progress, now), record.timeline)


def _row(
    record: AssignmentRecord,
    grants: list[ExtensionGrant],
    progress: Progress,
    summary: str,
    size: int,
    now: datetime,
) -> AssignmentRow:
    settings = record.settings
    return AssignmentRow(
        record=record,
        state=_state(record, grants, progress, now),
        ends_at=assignment_end(record.timeline, grants),
        audience_count=size,
        audience_summary=summary,
        progress=progress,
        publication_state=publication_state(settings.publication, record.published_at),
        locked=is_locked(record.timeline, has_password=record.has_password),
    )


def _picked_groups(records: Sequence[AssignmentRecord]) -> dict[UUID, PickedGroup]:
    group_ids = list(dict.fromkeys(g for record in records for g in record.source_group_ids))
    if not group_ids:
        return {}
    rosters = students.list_group_rosters(group_ids)
    return {r.group_id: (r.name, r.active_member_ids) for r in rosters}


def _state(
    record: AssignmentRecord, grants: list[ExtensionGrant], progress: Progress, now: datetime
) -> LifecycleState:
    return lifecycle_state(
        record.timeline, grants, now=now, attempts_in_progress=progress.in_progress > 0
    )
