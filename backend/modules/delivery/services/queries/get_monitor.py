from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.monitor import MonitorFilter, MonitorStatus, is_shown, monitor_status
from modules.delivery.domain.timeline import attempt_deadline
from modules.delivery.policies import ensure_teacher
from modules.delivery.repositories import attempt_rows, attempts, responses, stage_progress
from modules.delivery.repositories.attempt_rows import AttemptRow
from modules.delivery.services.live import LiveAttempt, bring_up_to_date


@dataclass(frozen=True, slots=True)
class MonitorRow:
    student_id: UUID
    name: str
    status: MonitorStatus
    # The latest sitting, if any
    attempt: AttemptRow | None
    answered: int
    deadline_at: datetime | None


@dataclass(frozen=True, slots=True)
class Monitor:
    title: str
    rows: list[MonitorRow]
    summary: dict[MonitorStatus, int]
    total_questions: int
    ends_at: datetime | None
    server_now: datetime


def get_monitor(ctx: Ctx, *, assignment_id: UUID, chosen: MonitorFilter) -> Monitor:
    """T-10, polled every 10 s: each student's latest sitting, how far they are, warnings and
    when they were last heard from. Sittings whose time ran out end first (lazy
    finalization, database_schema.md §5.2). A fixed number of queries for any class size."""
    ensure_teacher(ctx.actor)
    frame = assignments.get_monitor_frame(ctx, assignment_id=assignment_id)
    deadlines = {a.attempt.id: _deadline(a) for a in _finalize(ctx, frame) if a.attempt.in_progress}
    latest = {row.student_id: row for row in attempt_rows.rows_of(assignment_id)}
    answered = responses.answered_counts([row.id for row in latest.values()])
    rows = [
        _row(member, latest.get(member.student_id), answered, deadlines) for member in frame.members
    ]
    return Monitor(
        title=frame.title,
        rows=[r for r in rows if is_shown(chosen, r.status, warnings=_warnings(r))],
        summary=dict(Counter(row.status for row in rows)),
        total_questions=frame.question_count,
        ends_at=frame.ends_at,
        server_now=ctx.now,
    )


def _finalize(ctx: Ctx, frame: assignments.MonitorFrame) -> list[LiveAttempt]:
    """Every sitting still running, brought up to date; one being written elsewhere is
    skipped (its deadline then shows on the next poll)."""
    with transaction.atomic():
        running = attempts.lock_running_of(frame.assignment_id, skip_locked=True)
        stages = stage_progress.stages_by_attempt([a.id for a in running])
        return [
            bring_up_to_date(ctx, a, frame.terms_for(a.student_id), stages[a.id]) for a in running
        ]


def _deadline(live: LiveAttempt) -> datetime:
    return attempt_deadline(live.clock)


def _row(
    member: assignments.MonitorMember,
    attempt: AttemptRow | None,
    answered: dict[UUID, int],
    deadlines: dict[UUID, datetime],
) -> MonitorRow:
    return MonitorRow(
        student_id=member.student_id,
        name=member.name,
        status=monitor_status(attempt.status, attempt.end_reason)
        if attempt
        else MonitorStatus.NOT_STARTED,
        attempt=attempt,
        answered=answered.get(attempt.id, 0) if attempt else 0,
        deadline_at=deadlines.get(attempt.id) if attempt else None,
    )


def _warnings(row: MonitorRow) -> int:
    return row.attempt.warning_count if row.attempt else 0
