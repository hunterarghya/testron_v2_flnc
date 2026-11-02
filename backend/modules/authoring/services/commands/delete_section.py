from enum import StrEnum
from uuid import UUID

from core.context import Ctx
from core.errors import FieldError, FieldsInvalid
from modules.authoring.domain.errors import SectionNotEmpty
from modules.authoring.repositories import questions, sections, tests_table
from modules.authoring.services.editing import EditResult, edit


class WithQuestions(StrEnum):
    """What happens to a deleted section's questions (api_contract.md §2.5)."""

    MOVE_TO_PREVIOUS = "move_to_previous"
    DELETE = "delete"


def delete_section(
    ctx: Ctx, *, section_id: UUID, revision: int, questions_choice: WithQuestions | None
) -> EditResult[None]:
    """Remove a section. Its questions join the section before it (the next one, for the
    first), or are deleted; with questions and no choice it's `section_not_empty`. The last
    section can't go (every test has one, domain_model.md §3.4 invariant 1)."""
    test_id = tests_table.owning_test_of_section(section_id)

    def change() -> None:
        layout = sections.layout(test_id)
        if len(layout) == 1:
            raise FieldsInvalid(
                FieldError("section_id", "last_section", "A test keeps at least one section")
            )
        index = [section for section, _ in layout].index(section_id)
        moving = layout[index][1]
        if moving and questions_choice is None:
            raise SectionNotEmpty(context={"question_count": len(moving)})
        rest = [entry for entry in layout if entry[0] != section_id]
        if questions_choice is WithQuestions.DELETE:
            questions.delete_questions(moving)
        elif moving:
            target = max(index - 1, 0)
            joined = [*rest[target][1], *moving] if index > 0 else [*moving, *rest[target][1]]
            rest[target] = (rest[target][0], joined)
        sections.apply_layout(rest)
        sections.delete_section(section_id)

    return edit(ctx, test_id, revision=revision, change=change)
