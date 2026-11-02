from uuid import UUID

from core.context import Ctx
from modules.authoring.domain.library import TestRow, row_of
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import tests_table
from modules.authoring.services.editing import read_document


def archive_test(ctx: Ctx, *, test_id: UUID) -> TestRow:
    """Hide a test from the library (T-02). Its assignments and results are untouched, and
    archiving twice changes nothing."""
    ensure_teacher(ctx.actor)
    if read_document(test_id).archived_at is None:
        tests_table.set_archived_at(test_id, ctx.now)
    return row_of(read_document(test_id))
