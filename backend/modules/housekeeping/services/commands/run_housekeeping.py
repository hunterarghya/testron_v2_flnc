from dataclasses import dataclass

from core import rate_limit
from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.housekeeping.domain.schedule import BATCH, cutoffs
from modules.identity import public as identity


@dataclass(frozen=True, slots=True)
class HousekeepingReport:
    otps: int
    rate_limits: int
    lobby_rows: int
    sessions: int
    attempts_ended: int


def run_housekeeping(ctx: Ctx) -> HousekeepingReport:
    """One bounded round of cleanup (database_schema.md §5.4): at most a batch of rows per
    table, each step in its own transaction, so a failure keeps what earlier steps did and
    the next run carries on. No policy: work no person asked for (system_ctx)."""
    due = cutoffs(ctx.now)
    return HousekeepingReport(
        otps=identity.delete_old_otps(created_before=due.otps_before, limit=BATCH),
        rate_limits=rate_limit.delete_stale(before=due.rate_limits_before, limit=BATCH),
        lobby_rows=assignments.delete_stale_lobby_presence(limit=BATCH),
        sessions=identity.delete_expired_sessions(now=ctx.now, limit=BATCH),
        attempts_ended=delivery.finalize_stale(
            ctx, anchored_before=due.abandoned_before, limit=BATCH
        ),
    )
