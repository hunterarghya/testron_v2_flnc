"""Moving between stages by the student's choice (domain_model.md §5.3; P-04, P-05). The
server applies both after catching up, so a stage that has already run out can't be gamed.

    move_next : leave the current stage (it closes unless returning is allowed) and enter
                the next; entering again keeps the first entry time, so its timer never resets.
    return_to : allow_return only, to a stage already entered and still running.
"""

from dataclasses import replace
from datetime import datetime

from modules.delivery.domain.errors import StageClosed, StageNavigationInvalid
from modules.delivery.domain.stages import Progress, StageTimes
from modules.delivery.domain.timeline import Clock, stage_deadline


def move_next(
    clock: Clock, progress: Progress, *, from_stage: int, allow_return: bool, now: datetime
) -> Progress:
    """Safe to repeat: a retry for a move already made changes nothing."""
    if from_stage < progress.current:
        return progress
    if from_stage != progress.current or progress.current >= clock.last:
        raise StageNavigationInvalid()
    stages = list(progress.stages)
    stages[from_stage] = _leave(stages[from_stage], now=now, close=not allow_return)
    following = from_stage + 1
    stages[following] = replace(stages[following], entered_at=stages[following].entered_at or now)
    return Progress(tuple(stages), following, max(progress.furthest, following))


def return_to(
    clock: Clock, progress: Progress, *, index: int, allow_return: bool, now: datetime
) -> Progress:
    """Back to a stage left earlier, or forward again to the furthest one reached."""
    if index == progress.current:
        return progress
    target = progress.stages[index] if 0 <= index <= progress.furthest else None
    if not allow_return or target is None or target.entered_at is None:
        raise StageNavigationInvalid()
    if target.closed_at is not None or stage_deadline(clock, index, target.entered_at) <= now:
        raise StageClosed(index)
    stages = list(progress.stages)
    stages[progress.current] = _leave(stages[progress.current], now=now, close=False)
    return Progress(tuple(stages), index, progress.furthest)


def _leave(stage: StageTimes, *, now: datetime, close: bool) -> StageTimes:
    return replace(stage, left_at=now, closed_at=now if close else stage.closed_at)
