from uuid import UUID

from core.context import Ctx
from modules.delivery.domain.navigation import move_next
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.stage_moves import move_stage


def move_to_next_stage(
    ctx: Ctx, *, attempt_id: UUID, from_stage_index: int, client_id: UUID | None
) -> AttemptStateView:
    """P-04 "Next section" and P-05 "Next" (domain_model.md §5.3): the stage left closes
    unless returning is allowed (in rapid fire that locks the answer). Safe to repeat for
    the same `from_stage_index`."""
    return move_stage(
        ctx,
        attempt_id=attempt_id,
        client_id=client_id,
        move=lambda live, paper: move_next(
            live.clock,
            live.progress,
            from_stage=from_stage_index,
            allow_return=paper.allow_return,
            now=ctx.now,
        ),
    )
