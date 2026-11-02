from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.library import QuestionSearchRow
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import library
from modules.authoring.services.editing import matching_tag_ids, tag_names


@dataclass(frozen=True, slots=True)
class QuestionPage:
    rows: list[QuestionSearchRow]
    total: int


def search_questions(
    ctx: Ctx,
    *,
    search: str | None,
    tag_id: UUID | None,
    exclude_test_id: UUID | None,
    offset: int,
    limit: int,
) -> QuestionPage:
    """Questions from other tests to import (T-03 Import, [C-12]): by their text or tags,
    the most recently edited first."""
    ensure_teacher(ctx.actor)
    text = search.strip() if search else None
    ids, total = library.search_question_ids(
        search=text,
        search_tag_ids=matching_tag_ids(text) if text else [],
        tag_id=tag_id,
        exclude_test_id=exclude_test_id,
        offset=offset,
        limit=limit,
    )
    return QuestionPage(rows=library.question_rows(ids, tag_names=tag_names), total=total)
