from dataclasses import dataclass

from core.context import Ctx
from modules.results.policies import ensure_teacher
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class Badges:
    pending_students: int
    results_to_publish: int


def get_badges(ctx: Ctx) -> Badges:
    """The numbers on the teacher's menu (screens.md, teacher shell), polled every 60 s.

    Results to publish come with assignments and grading (Phases 5 to 7); until then, 0.
    """
    ensure_teacher(ctx.actor)
    return Badges(pending_students=students.count_pending_students(), results_to_publish=0)
