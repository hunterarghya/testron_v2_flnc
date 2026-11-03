from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from core.errors import NotFound
from core.rich_content import Json
from modules.delivery.domain.attempt import AttemptRecord
from modules.delivery.domain.plan import read_plan
from modules.delivery.domain.values import AttemptStatus, EndReason
from modules.delivery.models import Attempt


@dataclass(frozen=True, slots=True)
class NewAttempt:
    assignment_id: UUID
    student_id: UUID
    take_number: int
    is_granted: bool
    started_at: datetime
    anchor_at: datetime
    seed: int
    plan: Json
    current_stage_index: int
    max_score: Decimal
    active_client_id: UUID


def record_of(row: Attempt) -> AttemptRecord:
    return AttemptRecord(
        id=row.id,
        assignment_id=row.assignment_id,
        student_id=row.student_id,
        take_number=row.take_number,
        is_granted=row.is_granted,
        status=AttemptStatus(row.status),
        end_reason=EndReason(row.end_reason) if row.end_reason else None,
        started_at=row.started_at,
        anchor_at=row.anchor_at,
        ended_at=row.ended_at,
        plan=read_plan(row.plan),
        current_stage_index=row.current_stage_index,
        furthest_stage_index=row.furthest_stage_index,
        warning_count=row.warning_count,
        active_client_id=row.active_client_id,
    )


def insert_attempt(new: NewAttempt) -> AttemptRecord | None:
    """None when this student already has one in progress, or that take exists: a start at
    the same instant won (E-01). The savepoint keeps the caller's transaction usable."""
    try:
        with transaction.atomic():
            row = Attempt.objects.create(
                **{f: getattr(new, f) for f in NewAttempt.__dataclass_fields__},
                furthest_stage_index=new.current_stage_index,
                status=AttemptStatus.IN_PROGRESS.value,
                last_seen_at=new.started_at,
            )
    except IntegrityError:
        return None
    return record_of(row)


def _mine(attempt_id: UUID, student_id: UUID, rows: QuerySet[Attempt]) -> AttemptRecord:
    """Someone else's attempt looks missing (A-03)."""
    row = rows.filter(pk=attempt_id, student_id=student_id).first()
    if row is None:
        raise NotFound("attempt")
    return record_of(row)


def get_for_student(attempt_id: UUID, student_id: UUID) -> AttemptRecord:
    return _mine(attempt_id, student_id, Attempt.objects.all())


def lock_for_student(attempt_id: UUID, student_id: UUID) -> AttemptRecord:
    """Ending, stage moves and takeovers wait for each other (database_schema.md §5.1)."""
    return _mine(attempt_id, student_id, Attempt.objects.select_for_update())


def lock_for_save(attempt_id: UUID, student_id: UUID) -> AttemptRecord:
    """Saves can't interleave with an ending, yet don't block key checks (ADR-043)."""
    return _mine(attempt_id, student_id, Attempt.objects.select_for_update(no_key=True))


def lock_in_progress(assignment_id: UUID, student_id: UUID) -> AttemptRecord | None:
    row = (
        Attempt.objects.select_for_update()
        .filter(
            assignment_id=assignment_id, student_id=student_id, status=AttemptStatus.IN_PROGRESS
        )
        .first()
    )
    return None if row is None else record_of(row)


def lock_expirable(attempt_ids: list[UUID]) -> list[AttemptRecord]:
    """These sittings, if still in progress; one being ended elsewhere is skipped, so two
    readers never wait for each other (database_schema.md §5.2)."""
    rows = Attempt.objects.select_for_update(skip_locked=True).filter(
        pk__in=attempt_ids, status=AttemptStatus.IN_PROGRESS
    )
    return [record_of(row) for row in rows]


def set_active_client(attempt_id: UUID, client_id: UUID) -> None:
    Attempt.objects.filter(pk=attempt_id).update(active_client_id=client_id)


def save_position(attempt_id: UUID, *, current: int, furthest: int, now: datetime) -> None:
    Attempt.objects.filter(pk=attempt_id).update(
        current_stage_index=current, furthest_stage_index=furthest, last_seen_at=now
    )


def touch(attempt_id: UUID, *, now: datetime) -> None:
    """The monitor's "Last seen" (database_schema.md §3.6)."""
    Attempt.objects.filter(pk=attempt_id).update(last_seen_at=now)


def mark_ended(  # keyword-only after the id (CLAUDE.md limits)
    attempt_id: UUID,
    *,
    reason: EndReason,
    ended_at: datetime,
    score: Decimal,
    answer_key_version: int,
    graded_at: datetime,
) -> None:
    """Ended and graded in one write (the attempts_end_shape constraint)."""
    Attempt.objects.filter(pk=attempt_id, status=AttemptStatus.IN_PROGRESS).update(
        status=AttemptStatus.ENDED.value,
        end_reason=reason.value,
        ended_at=ended_at,
        score=score,
        answer_key_version=answer_key_version,
        graded_at=graded_at,
    )


def set_warning_count(attempt_id: UUID, count: int) -> None:
    Attempt.objects.filter(pk=attempt_id).update(warning_count=count)
