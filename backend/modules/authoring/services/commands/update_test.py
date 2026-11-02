from typing import TypedDict
from uuid import UUID

from core.context import Ctx
from core.errors import FieldError, FieldsInvalid
from core.text import clean_text_line
from modules.authoring.domain.document import TestDocumentView
from modules.authoring.domain.settings_patch import (
    SettingsChange,
    SettingsPatch,
    apply_settings_patch,
)
from modules.authoring.domain.structure import merged
from modules.authoring.models.test import MAX_TITLE_LENGTH
from modules.authoring.repositories import sections, tests_table
from modules.authoring.services.editing import EditResult, edit, read_document, rich


class TestChanges(TypedDict, total=False):
    title: str
    # None removes the instructions
    instructions: object
    settings: SettingsPatch


def update_test(
    ctx: Ctx, *, test_id: UUID, revision: int, changes: TestChanges
) -> EditResult[None]:
    """Change the title, instructions or settings (T-03 toolbar, T-04). A new timing kind may
    merge the sections into one (domain_model.md §3.4 invariant 1, ADR-062)."""
    values: dict[str, object] = {}
    if "title" in changes:
        values["title"] = _title(changes["title"])
    if "instructions" in changes:
        raw = changes["instructions"]
        values["instructions"] = None if raw is None else rich("instructions", raw)

    def change() -> None:
        if "settings" in changes:
            values.update(_apply_settings(test_id, changes["settings"]))
        tests_table.update_test(test_id, values)

    return edit(ctx, test_id, revision=revision, change=change)


def _title(raw: str) -> str:
    title = clean_text_line(raw)
    if not title or len(title) > MAX_TITLE_LENGTH:
        raise FieldsInvalid(
            FieldError("title", "invalid", f"Use 1 to {MAX_TITLE_LENGTH} characters")
        )
    return title


def _apply_settings(test_id: UUID, patch: SettingsPatch) -> dict[str, object]:
    document = read_document(test_id)
    durations = [section.duration_s for section in document.sections]
    result = apply_settings_patch(document.settings, patch, section_durations=durations)
    _reshape_sections(test_id, result, document)
    return tests_table.settings_columns(result.settings)


def _reshape_sections(test_id: UUID, result: SettingsChange, before: TestDocumentView) -> None:
    switch = result.switch
    if switch is None:
        return
    current = sections.layout(test_id)
    if switch.merge_sections and len(current) > 1:
        sections.apply_layout(merged(current))
        sections.delete_sections([section_id for section_id, _ in current[1:]])
    # Only fills a missing duration; one the teacher set stays
    first = before.sections[0]
    if switch.section_duration_s is not None and len(current) == 1 and first.duration_s is None:
        sections.update_section(first.id, {"duration_s": switch.section_duration_s})
