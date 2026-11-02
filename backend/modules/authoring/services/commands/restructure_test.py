from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.structure import Layout, ensure_same_structure
from modules.authoring.repositories import sections
from modules.authoring.services.editing import EditResult, edit


def restructure_test(ctx: Ctx, *, test_id: UUID, revision: int, wanted: Layout) -> EditResult[None]:
    """Reorder sections and questions, including moving questions between sections (T-03
    drag and drop). The new layout must name exactly the test's sections and questions."""

    def change() -> None:
        ensure_same_structure(sections.layout(test_id), wanted)
        sections.apply_layout(wanted)

    return edit(ctx, test_id, revision=revision, change=change)
