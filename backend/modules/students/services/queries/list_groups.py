from core.context import Ctx
from modules.students.domain.values import GroupSummary
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups


def list_groups(ctx: Ctx, *, archived: bool, search: str | None) -> list[GroupSummary]:
    """The Groups page and every group picker (T-16): active groups by default, by name, each
    with its member count. One query, however many groups."""
    ensure_teacher(ctx.actor)
    return groups.list_group_summaries(archived=archived, search=search)
