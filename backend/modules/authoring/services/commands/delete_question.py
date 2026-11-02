from uuid import UUID

from core.context import Ctx
from modules.authoring.repositories import questions, sections, tests_table
from modules.authoring.services.editing import EditResult, edit


def delete_question(ctx: Ctx, *, question_id: UUID, revision: int) -> EditResult[None]:
    """Remove a question and close the gap it leaves (T-03). Assigned papers keep their own
    copy, so this never changes an assignment (domain_model.md §3.4, [C-11])."""
    test_id = tests_table.owning_test_of_question(question_id)

    def change() -> None:
        questions.delete_questions([question_id])
        sections.apply_layout(sections.layout(test_id))

    return edit(ctx, test_id, revision=revision, change=change)
