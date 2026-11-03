from collections.abc import Sequence
from uuid import UUID

from modules.delivery.domain.stages import StageTimes
from modules.delivery.models import StageProgress


def insert_stages(attempt_id: UUID, stages: Sequence[StageTimes]) -> None:
    """Every stage gets its row at the start (database_schema.md §3.6)."""
    StageProgress.objects.bulk_create(
        [
            StageProgress(
                attempt_id=attempt_id,
                stage_index=index,
                entered_at=stage.entered_at,
                left_at=stage.left_at,
                closed_at=stage.closed_at,
                missed=stage.missed,
            )
            for index, stage in enumerate(stages)
        ]
    )


def stages_of(attempt_id: UUID) -> tuple[StageTimes, ...]:
    rows = (
        StageProgress.objects.filter(attempt_id=attempt_id)
        .order_by("stage_index")
        .values_list("entered_at", "left_at", "closed_at", "missed")
    )
    return tuple(StageTimes(*row) for row in rows)


def stages_by_attempt(attempt_ids: Sequence[UUID]) -> dict[UUID, tuple[StageTimes, ...]]:
    found: dict[UUID, list[StageTimes]] = {attempt_id: [] for attempt_id in attempt_ids}
    rows = (
        StageProgress.objects.filter(attempt_id__in=attempt_ids)
        .order_by("attempt_id", "stage_index")
        .values_list("attempt_id", "entered_at", "left_at", "closed_at", "missed")
    )
    for attempt_id, entered_at, left_at, closed_at, missed in rows:
        found[attempt_id].append(StageTimes(entered_at, left_at, closed_at, missed))
    return {attempt_id: tuple(stages) for attempt_id, stages in found.items()}


def save_changes(
    attempt_id: UUID, before: Sequence[StageTimes], after: Sequence[StageTimes]
) -> None:
    """Only the stages that changed: usually one or two per auto-advance."""
    for index, (old, new) in enumerate(zip(before, after, strict=True)):
        if old != new:
            StageProgress.objects.filter(attempt_id=attempt_id, stage_index=index).update(
                entered_at=new.entered_at, left_at=new.left_at, closed_at=new.closed_at
            )
