from collections.abc import Sequence
from uuid import UUID

from core.context import Ctx
from core.errors import FieldError, FieldsInvalid, NotFound
from modules.authoring.domain.structure import insert_after
from modules.authoring.repositories import questions, sections
from modules.authoring.services.editing import EditResult, edit

MAX_IMPORT = 100


def import_questions(
    ctx: Ctx,
    *,
    test_id: UUID,
    revision: int,
    source_question_ids: Sequence[UUID],
    section_id: UUID,
    after_question_id: UUID | None,
) -> EditResult[list[UUID]]:
    """Copy questions from other tests in at the cursor, in the order ticked (T-03 Import,
    [C-12]). The copies are independent: editing them never changes the originals."""
    unique = len(set(source_question_ids)) == len(source_question_ids)
    if not unique or not source_question_ids or len(source_question_ids) > MAX_IMPORT:
        raise FieldsInvalid(
            FieldError(
                "source_question_ids", "invalid", f"Pick 1 to {MAX_IMPORT} different questions"
            )
        )

    def change() -> list[UUID]:
        layout = dict(sections.layout(test_id))
        if section_id not in layout:
            raise NotFound("section")
        start = len(layout[section_id])
        targets = [
            questions.CopyTo(source, test_id, section_id, start + i)
            for i, source in enumerate(source_question_ids)
        ]
        copies = questions.copy_questions(targets, now=ctx.now)
        placed = layout[section_id]
        for copy_id in reversed(copies):
            placed = insert_after(placed, copy_id, after_question_id)
        layout[section_id] = placed
        sections.apply_layout(list(layout.items()))
        return copies

    return edit(ctx, test_id, revision=revision, change=change)
