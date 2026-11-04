from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx
from core.errors import NotFound
from modules.delivery import public as delivery
from modules.results.policies import ensure_teacher
from modules.results.services.performance_view import PerformanceView, group_performance_of
from modules.results.services.standings import counts
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class GroupPerformanceView:
    group_name: str
    students: int
    report: PerformanceView


def get_group_performance(ctx: Ctx, *, group_id: UUID) -> GroupPerformanceView:
    """T-17's performance tab (domain_model.md §6.5): the class's weak chapters, from every
    counted attempt of everyone in the group, and each test's score % over time."""
    ensure_teacher(ctx.actor)
    rosters = students.list_group_rosters([group_id])
    if not rosters:
        raise NotFound("group")
    members = students.list_group_member_ids(group_id)
    attempts = [a for a in delivery.rows_of_students(list(members)) if counts(a)]
    return GroupPerformanceView(rosters[0].name, len(members), group_performance_of(attempts))
