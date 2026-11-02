from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.structure import insert_after
from modules.authoring.repositories import questions, sections, tests_table
from modules.authoring.services.editing import EditResult, edit


def duplicate_question(ctx: Ctx, *, question_id: UUID, revision: int) -> EditResult[UUID]:
    """A copy right after the original, with its options and tags (T-03 `⋯` Duplicate)."""
    test_id = tests_table.owning_test_of_question(question_id)

    def change() -> UUID:
        layout = dict(sections.layout(test_id))
        section_id = next(sid for sid, ids in layout.items() if question_id in ids)
        copy_id = questions.copy_question(
            question_id, position=len(layout[section_id]), now=ctx.now
        )
        layout[section_id] = insert_after(layout[section_id], copy_id, question_id)
        sections.apply_layout(list(layout.items()))
        return copy_id

    return edit(ctx, test_id, revision=revision, change=change)
