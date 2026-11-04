from dataclasses import dataclass

from core.context import Ctx
from modules.results.policies import ensure_teacher
from modules.results.services.queries.list_results_inbox import InboxTab, list_results_inbox
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class Badges:
    pending_students: int
    results_to_publish: int


def get_badges(ctx: Ctx) -> Badges:
    """The numbers on the teacher's menu (screens.md, teacher shell), polled every 60 s: the
    students waiting for approval and T-13's "To publish" tab."""
    ensure_teacher(ctx.actor)
    to_publish = len(list_results_inbox(ctx, tab=InboxTab.TO_PUBLISH))
    return Badges(pending_students=students.count_pending_students(), results_to_publish=to_publish)
