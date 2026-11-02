from collections.abc import Sequence
from uuid import UUID

from core.context import Ctx
from modules.students.domain.values import AudienceCandidate
from modules.students.policies import ensure_teacher
from modules.students.repositories import memberships


def preview_audience(ctx: Ctx, *, group_ids: Sequence[UUID]) -> list[AudienceCandidate]:
    """Who the assignment wizard would add for these groups (T-07 step 2): their ACTIVE
    students, each once, with every chosen group they belong to. The teacher confirms this
    list; the saved audience never follows later group changes (ADR-016)."""
    ensure_teacher(ctx.actor)
    return memberships.active_students_in_groups(list(dict.fromkeys(group_ids)))
