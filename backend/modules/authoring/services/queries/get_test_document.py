from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.document import TestDocumentView
from modules.authoring.policies import ensure_teacher
from modules.authoring.services.editing import read_document


def get_test_document(ctx: Ctx, *, test_id: UUID) -> TestDocumentView:
    """The whole test for the editor (T-03), correct answers and solutions included, with its
    problems and totals. Six queries, however long the test is."""
    ensure_teacher(ctx.actor)
    return read_document(test_id)
