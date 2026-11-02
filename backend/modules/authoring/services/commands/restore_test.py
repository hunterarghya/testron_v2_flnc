from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.library import TestRow, row_of
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tests_table
from modules.authoring.services.editing import read_document


def restore_test(ctx: Ctx, *, test_id: UUID) -> TestRow:
    """Bring an archived test back to the library (T-02). Safe to repeat."""
    ensure_teacher(ctx.actor)
    tests_table.set_archived_at(test_id, None)
    return row_of(read_document(test_id))
