from core.context import Ctx
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tag_usage
from modules.tagging import public as tagging


def suggest_tags(ctx: Ctx, *, kind: tagging.TagKind, typed: str) -> list[tagging.TagRef]:
    """Up to 8 tags for what the teacher is typing in a tag pill (domain_model.md §4.1, T-03):
    names starting with it first, then names containing it, the most used first."""
    ensure_teacher(ctx.actor)
    query = tagging.normalize_tag_name(typed)
    candidates = tagging.list_tags(kind, search=query)
    usage = tag_usage.question_counts([tag.id for tag in candidates])
    return tagging.rank_suggestions(candidates, typed, usage)
