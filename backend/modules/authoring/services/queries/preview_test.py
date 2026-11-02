from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.preview import PreviewPaper, preview_paper
from modules.authoring.policies import ensure_teacher
from modules.authoring.services.editing import read_document


def preview_test(ctx: Ctx, *, test_id: UUID, show_answers: bool) -> PreviewPaper:
    """The test as a student will see it (T-05), even while it still has problems."""
    ensure_teacher(ctx.actor)
    return preview_paper(read_document(test_id), show_answers=show_answers)
