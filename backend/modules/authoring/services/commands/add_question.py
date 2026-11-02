from uuid import UUID

from core.context import Ctx
from core.errors import NotFound
from core.rich_content import EMPTY_DOC
from modules.authoring.domain.structure import insert_after
from modules.authoring.domain.values import QuestionType
from modules.authoring.repositories import questions, sections
from modules.authoring.services.editing import EditResult, edit

# A new choice question starts with four empty options (A-D), as on paper
NEW_OPTIONS = 4


def add_question(
    ctx: Ctx,
    *,
    test_id: UUID,
    revision: int,
    section_id: UUID,
    after_question_id: UUID | None,
    question_type: QuestionType,
) -> EditResult[UUID]:
    """A new, empty question after the given one (T-03 slash menu: MCQ, MSQ, Numerical)."""

    def change() -> UUID:
        layout = dict(sections.layout(test_id))
        if section_id not in layout:
            raise NotFound("section")
        new_id = questions.insert_question(
            test_id,
            section_id,
            position=len(layout[section_id]),
            values={"type": question_type.value, "stem": EMPTY_DOC},
            now=ctx.now,
        )
        if question_type is not QuestionType.NUMERICAL:
            questions.insert_options(new_id, [(EMPTY_DOC, False)] * NEW_OPTIONS)
        layout[section_id] = insert_after(layout[section_id], new_id, after_question_id)
        sections.apply_layout(list(layout.items()))
        return new_id

    return edit(ctx, test_id, revision=revision, change=change)
