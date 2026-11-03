"""An attempt brought up to date: the auto-advances due by now applied, and ended at its
deadline if its time ran out (lazy finalization, domain_model.md §5.3, §5.5). Every exam-hall
use case starts here, with the attempt locked, inside its own transaction."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.attempt import AttemptRecord, end_reason_at_deadline
from modules.delivery.domain.paper import PaperView, read_paper
from modules.delivery.domain.stages import Progress, StageTimes, catch_up
from modules.delivery.domain.timeline import Clock, Extension
from modules.delivery.domain.values import EndReason, Notice
from modules.delivery.repositories import attempts, stage_progress
from modules.delivery.services.commands.end_attempt import end_attempt


class Terms(Protocol):
    """The assignment's side of the clock: a SittingTerms or a StudentAssignment."""

    @property
    def window(self) -> assignments.Window: ...
    @property
    def ended_at(self) -> datetime | None: ...
    @property
    def extensions(self) -> tuple[assignments.ExtensionGrant, ...]: ...


@dataclass(frozen=True, slots=True)
class LiveAttempt:
    attempt: AttemptRecord
    clock: Clock
    progress: Progress
    notice: Notice | None = None


def clock_for(
    terms: Terms, *, anchor_at: datetime, durations_s: tuple[int, ...], granted: bool
) -> Clock:
    """A granted sitting ignores a deadline window's close (§5.7)."""
    window = terms.window
    capped = window.kind is assignments.WindowKind.DEADLINE and not granted
    return Clock(
        anchor_at=anchor_at,
        durations_s=durations_s,
        extensions=tuple(Extension(e.seconds, e.stage_index) for e in terms.extensions),
        closes_at=window.closes_at if capped else None,
        ended_at=terms.ended_at,
    )


def clock_of(attempt: AttemptRecord, terms: Terms) -> Clock:
    return clock_for(
        terms,
        anchor_at=attempt.anchor_at,
        durations_s=attempt.plan.durations_s,
        granted=attempt.is_granted,
    )


def open_live(ctx: Ctx, attempt: AttemptRecord, terms: Terms) -> LiveAttempt:
    return bring_up_to_date(ctx, attempt, terms, stage_progress.stages_of(attempt.id))


def bring_up_to_date(
    ctx: Ctx, attempt: AttemptRecord, terms: Terms, stages: Sequence[StageTimes]
) -> LiveAttempt:
    clock = clock_of(attempt, terms)
    progress = Progress(tuple(stages), attempt.current_stage_index, attempt.furthest_stage_index)
    if not attempt.in_progress:
        return LiveAttempt(attempt, clock, progress, _ending_notice(attempt))
    caught = catch_up(clock, progress, now=ctx.now)
    stage_progress.save_changes(attempt.id, progress.stages, caught.progress.stages)
    moved = caught.progress.current != progress.current
    if caught.ended_at is not None:
        reason = end_reason_at_deadline(caught.ended_at, ended_for_everyone_at=terms.ended_at)
        ended = end_attempt(attempt, reason=reason, ended_at=caught.ended_at, now=ctx.now)
        return LiveAttempt(ended, clock, caught.progress, _ending_notice(ended))
    if not moved:
        return LiveAttempt(attempt, clock, caught.progress)
    current, furthest = caught.progress.current, caught.progress.furthest
    attempts.save_position(attempt.id, current=current, furthest=furthest, now=ctx.now)
    advanced = replace(attempt, current_stage_index=current, furthest_stage_index=furthest)
    return LiveAttempt(advanced, clock, caught.progress, Notice.STAGE_ADVANCED)


def _ending_notice(attempt: AttemptRecord) -> Notice | None:
    return Notice.ENDED_BY_TEACHER if attempt.end_reason is EndReason.ENDED_BY_TEACHER else None


def paper_of(attempt: AttemptRecord) -> PaperView:
    return read_paper(assignments.get_paper_content(attempt.assignment_id))
