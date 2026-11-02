from dataclasses import dataclass

from core.context import Ctx
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tag_usage
from modules.tagging import public as tagging


@dataclass(frozen=True, slots=True)
class TagUsage:
    tag: tagging.TagRef
    question_count: int
    test_count: int


def list_tags_with_usage(
    ctx: Ctx, *, kind: tagging.TagKind | None, search: str | None
) -> list[TagUsage]:
    """The Tags page (T-18): every tag, by kind and name, with how many questions and tests
    use it. Tags are created only in the editor, so there is no "new tag" here."""
    ensure_teacher(ctx.actor)
    tags = tagging.list_tags(kind, search=tagging.normalize_tag_name(search) if search else None)
    ids = [tag.id for tag in tags]
    questions, tests = tag_usage.question_counts(ids), tag_usage.test_counts(ids)
    return [TagUsage(tag, questions[tag.id], tests[tag.id]) for tag in tags]
