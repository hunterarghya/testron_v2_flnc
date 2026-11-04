from dataclasses import dataclass
from datetime import datetime, timedelta

from core.context import Ctx
from modules.assignments import public as assignments
from modules.results.policies import ensure_teacher
from modules.results.services.queries.list_results_inbox import (
    InboxRow,
    InboxTab,
    list_results_inbox,
)
from modules.students import public as students

# "Upcoming" looks a week ahead; "Recent results" shows the newest few (T-01)
UPCOMING_DAYS = 7
RECENT_COUNT = 5


@dataclass(frozen=True, slots=True)
class Dashboard:
    live: list[assignments.AssignmentRow]
    upcoming: list[assignments.AssignmentRow]
    recent: list[InboxRow]
    pending_students: int
    results_to_publish: int


def get_dashboard(ctx: Ctx) -> Dashboard:
    """T-01, polled every 15 s: what is running, what comes this week, the latest results and
    what needs the teacher (students to approve, results to publish)."""
    ensure_teacher(ctx.actor)
    rows = assignments.list_assignments(
        ctx, filters=assignments.AssignmentFilter(), offset=0, limit=10_000
    ).rows
    inbox = list_results_inbox(ctx, tab=InboxTab.ALL)
    return Dashboard(
        live=[r for r in rows if r.state.value == "LIVE"],
        upcoming=sorted(
            (r for r in rows if _is_upcoming(r, ctx.now)), key=lambda r: _when(r) or ctx.now
        ),
        recent=inbox[:RECENT_COUNT],
        pending_students=students.count_pending_students(),
        results_to_publish=sum(r.row.publication_state.value == "UNPUBLISHED" for r in inbox),
    )


def _when(row: assignments.AssignmentRow) -> datetime | None:
    window = row.record.settings.window
    return window.starts_at or window.opens_at or window.planned_at


def _is_upcoming(row: assignments.AssignmentRow, now: datetime) -> bool:
    """Not started yet, and either within the week or with no time set (a locked test)."""
    if row.state.value not in ("SCHEDULED", "WAITING"):
        return False
    when = _when(row)
    return when is None or when < now + timedelta(days=UPCOMING_DAYS)
