"""Where the student is among the stages (domain_model.md §5.3-5.4, §7.4): entering at the
start, and the auto-advances the server applies lazily, at the deadline instants rather than
"now", so being offline never steals or gifts time."""

from dataclasses import dataclass, replace
from datetime import datetime

from modules.delivery.domain.errors import EntryClosed, QuestionNotInStage, StageClosed
from modules.delivery.domain.timeline import Clock, boundary, stage_deadline
from modules.delivery.domain.values import StageState


@dataclass(frozen=True, slots=True)
class StageTimes:
    # The first entry only
    entered_at: datetime | None = None
    left_at: datetime | None = None
    closed_at: datetime | None = None
    # A late joiner arrived after this stage's boundary
    missed: bool = False


@dataclass(frozen=True, slots=True)
class Progress:
    stages: tuple[StageTimes, ...]
    current: int
    furthest: int


@dataclass(frozen=True, slots=True)
class CatchUp:
    progress: Progress
    # When the attempt ran out of time; None while it still has some
    ended_at: datetime | None = None


def opening(clock: Clock, *, now: datetime) -> Progress:
    """The stages at the start: enter the first stage whose boundary is still ahead. On a
    shared clock a late joiner misses the stages already past (E-07); on an own clock the
    anchor is now, so nothing is missed."""
    entry = max(now, clock.anchor_at)
    first = next(
        (i for i in range(clock.last + 1) if boundary(clock, i) > entry),
        None,
    )
    if first is None:
        raise EntryClosed(closed_at=boundary(clock, clock.last))
    missed = tuple(StageTimes(closed_at=boundary(clock, i), missed=True) for i in range(first))
    entered = StageTimes(entered_at=entry)
    later = tuple(StageTimes() for _ in range(first + 1, clock.last + 1))
    return Progress(stages=(*missed, entered, *later), current=first, furthest=first)


def catch_up(clock: Clock, progress: Progress, *, now: datetime) -> CatchUp:
    """Apply every auto-advance due by `now`: the current stage closes at its deadline and the
    next is entered at that instant; when the last one runs out, the attempt has ended then."""
    stages = list(_close_expired(clock, progress.stages, now))
    index, furthest, at = progress.current, progress.furthest, None
    while (deadline := stage_deadline(clock, index, stages[index].entered_at)) <= now:
        at = deadline if at is None else max(at, deadline)
        stage = stages[index]
        stages[index] = replace(stage, left_at=stage.left_at or at, closed_at=stage.closed_at or at)
        if index == clock.last:
            return CatchUp(Progress(tuple(stages), index, furthest), ended_at=at)
        index += 1
        furthest = max(furthest, index)
        if stages[index].entered_at is None:
            stages[index] = replace(stages[index], entered_at=at)
    return CatchUp(Progress(tuple(stages), index, furthest))


def _close_expired(
    clock: Clock, stages: tuple[StageTimes, ...], now: datetime
) -> tuple[StageTimes, ...]:
    """Stages left behind (allow_return) close at their own deadline."""
    return tuple(
        replace(stage, closed_at=deadline)
        if stage.entered_at is not None
        and stage.closed_at is None
        and (deadline := stage_deadline(clock, i, stage.entered_at)) <= now
        else stage
        for i, stage in enumerate(stages)
    )


def stage_state(clock: Clock, progress: Progress, index: int, *, now: datetime) -> StageState:
    stage = progress.stages[index]
    if stage.missed:
        return StageState.MISSED
    if stage.entered_at is None:
        return StageState.NOT_ENTERED
    if stage.closed_at is not None or stage_deadline(clock, index, stage.entered_at) <= now:
        return StageState.CLOSED
    return StageState.OPEN if index == progress.current else StageState.LEFT


def deadline_at(clock: Clock, progress: Progress, index: int) -> datetime | None:
    """What the student's timer counts down to for this stage; None for a missed one."""
    stage = progress.stages[index]
    if stage.missed:
        return None
    return stage.closed_at or stage_deadline(clock, index, stage.entered_at)


def ensure_answerable(
    clock: Clock, progress: Progress, stage: int | None, *, now: datetime
) -> None:
    """A question may be answered while its stage is open, or left but still running
    (allow_return); never in a closed, missed or future stage (domain_model.md §3.6 #4)."""
    if stage is None:
        raise QuestionNotInStage()
    state = stage_state(clock, progress, stage, now=now)
    if state in (StageState.CLOSED, StageState.MISSED):
        raise StageClosed(stage)
    if state is StageState.NOT_ENTERED:
        raise QuestionNotInStage()
