from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.repositories import attempts, stage_progress
from modules.delivery.services.commands.finalize_expired import finalize_expired
from modules.delivery.services.live import LiveAttempt, bring_up_to_date


def finalize_assignment(ctx: Ctx, *, assignment_id: UUID) -> assignments.MonitorFrame:
    """Lazy finalization before the teacher's gradebook is read (database_schema.md §5.2).
    The assignment's frame checks the teacher; it is returned (the audience with names)."""
    frame = assignments.get_monitor_frame(ctx, assignment_id=assignment_id)
    finalize_running(ctx, frame)
    return frame


def finalize_running(ctx: Ctx, frame: assignments.MonitorFrame) -> list[LiveAttempt]:
    """Every sitting still running is brought up to date; those whose time ran out end at
    their deadline and are graded. One being written elsewhere is skipped, not waited for.
    Returns the sittings looked at."""
    with transaction.atomic():
        running = attempts.lock_running_of(frame.assignment_id, skip_locked=True)
        stages = stage_progress.stages_by_attempt([a.id for a in running])
        return [
            bring_up_to_date(ctx, a, frame.terms_for(a.student_id), stages[a.id]) for a in running
        ]


def finalize_student(ctx: Ctx, *, student_id: UUID) -> None:
    """The same before a student's Past Tests are read."""
    finalize_expired(ctx, student_id, assignments.list_student_assignments(student_id))
