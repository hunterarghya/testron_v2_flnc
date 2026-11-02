"""The Test Library (T-02), question search and import (T-03), and the preview (T-05)."""

from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Status

from core.http.context import ctx_from
from core.http.pagination import Page, PageIn
from modules.authoring.domain.library import LibrarySort, TestFilter
from modules.authoring.dto.document import TestDocumentOut
from modules.authoring.dto.library import (
    ImportIn,
    ImportOut,
    QuestionSearchIn,
    QuestionSearchRowOut,
    TestFilterIn,
    TestRowOut,
)
from modules.authoring.dto.preview import PreviewIn, PreviewOut
from modules.authoring.services.commands import archive_test as archiving
from modules.authoring.services.commands import duplicate_test as duplicating
from modules.authoring.services.commands import import_questions as importing
from modules.authoring.services.commands import restore_test as restoring
from modules.authoring.services.queries import list_tests as listing
from modules.authoring.services.queries import preview_test as previewing
from modules.authoring.services.queries import search_questions as searching


def list_tests(
    request: HttpRequest, filters: Query[TestFilterIn], page: Query[PageIn]
) -> Page[TestRowOut]:
    result = listing.list_tests(
        ctx_from(request),
        filters=TestFilter(
            archived=filters.status == "archived",
            search=filters.q,
            tag_id=filters.tag_id,
            sort=LibrarySort(filters.sort),
        ),
        offset=page.offset,
        limit=page.limit,
    )
    return Page[TestRowOut].of(
        [TestRowOut.from_row(r) for r in result.rows], page=page, total=result.total
    )


def duplicate_test(request: HttpRequest, test_id: UUID) -> Status[TestDocumentOut]:
    copy = duplicating.duplicate_test(ctx_from(request), test_id=test_id)
    return Status(201, TestDocumentOut.from_view(copy))


def archive_test(request: HttpRequest, test_id: UUID) -> TestRowOut:
    return TestRowOut.from_row(archiving.archive_test(ctx_from(request), test_id=test_id))


def restore_test(request: HttpRequest, test_id: UUID) -> TestRowOut:
    return TestRowOut.from_row(restoring.restore_test(ctx_from(request), test_id=test_id))


def preview_test(request: HttpRequest, test_id: UUID, params: Query[PreviewIn]) -> PreviewOut:
    paper = previewing.preview_test(
        ctx_from(request), test_id=test_id, show_answers=params.show_answers
    )
    return PreviewOut.from_paper(paper)


def search_questions(
    request: HttpRequest, filters: Query[QuestionSearchIn], page: Query[PageIn]
) -> Page[QuestionSearchRowOut]:
    result = searching.search_questions(
        ctx_from(request),
        search=filters.q,
        tag_id=filters.tag_id,
        exclude_test_id=filters.exclude_test_id,
        offset=page.offset,
        limit=page.limit,
    )
    rows = [QuestionSearchRowOut.from_row(r) for r in result.rows]
    return Page[QuestionSearchRowOut].of(rows, page=page, total=result.total)


def import_questions(request: HttpRequest, test_id: UUID, payload: ImportIn) -> ImportOut:
    result = importing.import_questions(
        ctx_from(request),
        test_id=test_id,
        revision=payload.revision,
        source_question_ids=payload.source_question_ids,
        section_id=payload.section_id,
        after_question_id=payload.after_question_id,
    )
    return ImportOut.with_questions(result)
