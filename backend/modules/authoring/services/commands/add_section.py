from uuid import UUID

from core.context import Ctx
from core.errors import FieldError, FieldsInvalid
from modules.authoring.domain.section_rules import section_duration, section_title
from modules.authoring.domain.structure import insert_after
from modules.authoring.domain.values import TimingKind
from modules.authoring.repositories import sections
from modules.authoring.services.editing import EditResult, edit, read_document


def add_section(
    ctx: Ctx,
    *,
    test_id: UUID,
    revision: int,
    after_section_id: UUID | None,
    title: str,
    duration_s: int | None,
) -> EditResult[UUID]:
    """A new, empty section after the given one (T-03 slash "Section"). Only sectioned tests
    have more than one section (domain_model.md §3.4 invariant 1)."""
    clean_title = section_title(title)
    checked_duration = section_duration(duration_s)

    def change() -> UUID:
        if read_document(test_id).settings.timing.kind is not TimingKind.SECTIONED:
            raise FieldsInvalid(
                FieldError(
                    "settings.timing", "not_sectioned", "Switch the test to sectioned timing first"
                )
            )
        order = sections.section_order(test_id)
        new_id = sections.insert_section(
            test_id, position=len(order), title=clean_title, duration_s=checked_duration
        )
        layout = dict(sections.layout(test_id))
        placed = insert_after(order, new_id, after_section_id)
        sections.apply_layout([(section_id, layout[section_id]) for section_id in placed])
        return new_id

    return edit(ctx, test_id, revision=revision, change=change)
