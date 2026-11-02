from dataclasses import dataclass, replace

from core.context import Ctx
from modules.authoring.domain.library import TestFilter, TestRow, row_of
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import library
from modules.authoring.services.editing import matching_tag_ids, read_documents


@dataclass(frozen=True, slots=True)
class TestPage:
    rows: list[TestRow]
    total: int


def list_tests(ctx: Ctx, *, filters: TestFilter, offset: int, limit: int) -> TestPage:
    """The Test Library (T-02): active or archived tests, searched by title or by the tags on
    their questions, with each test's counts and problems. A fixed number of queries, however
    many tests the page shows."""
    ensure_teacher(ctx.actor)
    text = filters.search.strip() if filters.search else None
    ids, total = library.list_test_ids(
        replace(filters, search=text),
        search_tag_ids=matching_tag_ids(text) if text else [],
        offset=offset,
        limit=limit,
    )
    documents = read_documents(ids)
    return TestPage(rows=[row_of(documents[test_id]) for test_id in ids], total=total)
