"""What the teacher's monitor, the gradebook and the student's past tests show of attempts:
never the paper or the plan."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.db.models import QuerySet

from core.errors import NotFound
from modules.delivery.domain.plan import Plan, read_plan
from modules.delivery.domain.values import AttemptStatus, EndReason
from modules.delivery.models import Attempt

_FIELDS = (
    "id",
    "assignment_id",
    "student_id",
    "take_number",
    "status",
    "end_reason",
    "started_at",
    "ended_at",
    "graded_at",
    "current_stage_index",
    "warning_count",
    "last_seen_at",
    "score",
    "max_score",
    "disqualification_overridden_at",
)


@dataclass(frozen=True, slots=True)
class AttemptRow:
    id: UUID
    assignment_id: UUID
    student_id: UUID
    take_number: int
    status: AttemptStatus
    end_reason: EndReason | None
    started_at: datetime
    ended_at: datetime | None
    graded_at: datetime | None
    current_stage_index: int
    warning_count: int
    last_seen_at: datetime
    score: Decimal | None
    max_score: Decimal
    disqualification_overridden_at: datetime | None


def _row(attempt: Attempt) -> AttemptRow:
    return AttemptRow(
        id=attempt.id,
        assignment_id=attempt.assignment_id,
        student_id=attempt.student_id,
        take_number=attempt.take_number,
        status=AttemptStatus(attempt.status),
        end_reason=EndReason(attempt.end_reason) if attempt.end_reason else None,
        started_at=attempt.started_at,
        ended_at=attempt.ended_at,
        graded_at=attempt.graded_at,
        current_stage_index=attempt.current_stage_index,
        warning_count=attempt.warning_count,
        last_seen_at=attempt.last_seen_at,
        score=attempt.score,
        max_score=attempt.max_score,
        disqualification_overridden_at=attempt.disqualification_overridden_at,
    )


def _rows(query: QuerySet[Attempt]) -> list[AttemptRow]:
    return [_row(row) for row in query.only(*_FIELDS)]


def rows_of(assignment_id: UUID) -> list[AttemptRow]:
    return _rows(
        Attempt.objects.filter(assignment_id=assignment_id).order_by("student_id", "take_number")
    )


def rows_of_assignments(assignment_ids: list[UUID]) -> list[AttemptRow]:
    return _rows(Attempt.objects.filter(assignment_id__in=assignment_ids))


def rows_of_students(student_ids: list[UUID]) -> list[AttemptRow]:
    return _rows(Attempt.objects.filter(student_id__in=student_ids).order_by("started_at"))


def rows_of_student(student_id: UUID) -> list[AttemptRow]:
    """Newest first (P-08)."""
    return _rows(Attempt.objects.filter(student_id=student_id).order_by("-started_at"))


def row_of(attempt_id: UUID) -> AttemptRow:
    found = Attempt.objects.filter(pk=attempt_id).only(*_FIELDS).first()
    if found is None:
        raise NotFound("attempt")
    return _row(found)


def plan_of(attempt_id: UUID) -> Plan:
    """The student's question and option order, to show a result as they saw it."""
    return read_plan(Attempt.objects.values_list("plan", flat=True).get(pk=attempt_id))
