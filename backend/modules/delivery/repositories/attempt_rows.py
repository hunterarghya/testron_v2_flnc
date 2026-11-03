"""What the teacher's monitor and summaries show of attempts: never the paper or the plan."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from core.errors import NotFound
from modules.delivery.domain.values import AttemptStatus, EndReason
from modules.delivery.models import Attempt

_FIELDS = (
    "id",
    "student_id",
    "take_number",
    "status",
    "end_reason",
    "ended_at",
    "current_stage_index",
    "warning_count",
    "last_seen_at",
    "score",
    "max_score",
)


@dataclass(frozen=True, slots=True)
class AttemptRow:
    id: UUID
    student_id: UUID
    take_number: int
    status: AttemptStatus
    end_reason: EndReason | None
    ended_at: datetime | None
    current_stage_index: int
    warning_count: int
    last_seen_at: datetime
    score: Decimal | None
    max_score: Decimal


def _row(attempt: Attempt) -> AttemptRow:
    return AttemptRow(
        id=attempt.id,
        student_id=attempt.student_id,
        take_number=attempt.take_number,
        status=AttemptStatus(attempt.status),
        end_reason=EndReason(attempt.end_reason) if attempt.end_reason else None,
        ended_at=attempt.ended_at,
        current_stage_index=attempt.current_stage_index,
        warning_count=attempt.warning_count,
        last_seen_at=attempt.last_seen_at,
        score=attempt.score,
        max_score=attempt.max_score,
    )


def rows_of(assignment_id: UUID) -> list[AttemptRow]:
    rows = Attempt.objects.filter(assignment_id=assignment_id).only(*_FIELDS)
    return [_row(row) for row in rows.order_by("student_id", "take_number")]


def row_of(attempt_id: UUID) -> AttemptRow:
    found = Attempt.objects.filter(pk=attempt_id).only(*_FIELDS).first()
    if found is None:
        raise NotFound("attempt")
    return _row(found)
