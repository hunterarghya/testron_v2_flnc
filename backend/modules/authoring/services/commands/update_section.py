from typing import TypedDict
from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.section_rules import section_duration, section_title
from modules.authoring.repositories import sections, tests_table
from modules.authoring.services.editing import EditResult, edit, rich


class SectionChanges(TypedDict, total=False):
    title: str
    # None removes them
    instructions: object
    # None clears it (a problem for sectioned tests, allowed in a draft)
    duration_s: int | None


def update_section(
    ctx: Ctx, *, section_id: UUID, revision: int, changes: SectionChanges
) -> EditResult[None]:
    """Rename a section, or change its instructions or duration (T-03 section header)."""
    test_id = tests_table.owning_test_of_section(section_id)
    values: dict[str, object] = {}
    if "title" in changes:
        values["title"] = section_title(changes["title"])
    if "instructions" in changes:
        raw = changes["instructions"]
        values["instructions"] = None if raw is None else rich("instructions", raw)
    if "duration_s" in changes:
        values["duration_s"] = section_duration(changes["duration_s"])
    return edit(
        ctx, test_id, revision=revision, change=lambda: sections.update_section(section_id, values)
    )
