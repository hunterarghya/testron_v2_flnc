from core.context import Ctx
from modules.housekeeping.domain.schedule import cutoffs
from modules.housekeeping.repositories import runs
from modules.housekeeping.services.commands.run_housekeeping import (
    HousekeepingReport,
    run_housekeeping,
)


def run_housekeeping_if_due(ctx: Ctx) -> HousekeepingReport | None:
    """Housekeeping without a cron (architecture.md §5.6): the first signed-in request ten
    minutes after the last run claims the next one; everyone else gets None at the cost of
    one small query."""
    if not runs.claim(now=ctx.now, due_after=cutoffs(ctx.now).due_after):
        return None
    return run_housekeeping(ctx)
