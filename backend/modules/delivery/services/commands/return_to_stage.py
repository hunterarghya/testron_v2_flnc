from uuid import UUID

from core.context import Ctx
from modules.delivery.domain.navigation import return_to
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.stage_moves import move_stage


def return_to_stage(
    ctx: Ctx, *, attempt_id: UUID, stage_index: int, client_id: UUID | None
) -> AttemptStateView:
    """P-04 section chips (domain_model.md §5.3, E-4): back to a section left earlier while
    its own timer still runs, only when the test allows returning. The section left stays
    open, and its timer keeps running [Q-7]."""
    return move_stage(
        ctx,
        attempt_id=attempt_id,
        client_id=client_id,
        move=lambda live, paper: return_to(
            live.clock,
            live.progress,
            index=stage_index,
            allow_return=paper.allow_return,
            now=ctx.now,
        ),
    )
