from core.context import Ctx
from core.text import clean_text_line
from modules.students.domain.groups import normalize_group_name
from modules.students.domain.values import GroupSummary
from modules.students.policies import ensure_teacher
from modules.students.repositories import groups


def create_group(ctx: Ctx, *, name: str, description: str) -> GroupSummary:
    """Create a group (T-16). Names are unique among active groups, ignoring case and extra
    spaces (domain_model.md §3.2); a taken name is a field error on `name`."""
    ensure_teacher(ctx.actor)
    group_id = groups.insert_group(
        name=name,
        normalized_name=normalize_group_name(name),
        description=clean_text_line(description),
        now=ctx.now,
    )
    return groups.get_group_summary(group_id)
