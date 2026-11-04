from urllib.parse import quote
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from ninja import Query

from core.http.context import ctx_from
from core.http.pagination import Page, PageIn
from modules.results.dto.answer_sheet import AnswerSheetOut
from modules.results.dto.dashboard import DashboardOut, ResultsInboxRowOut
from modules.results.dto.gradebook import GradebookOut, KeyedPaperOut, QuestionStatOut
from modules.results.dto.past_tests import PastTestOut
from modules.results.dto.queries import InboxIn, SheetsIn
from modules.results.dto.result import ResultOut
from modules.results.services.queries import export_gradebook_csv as exporting
from modules.results.services.queries import get_answer_key_view as keys
from modules.results.services.queries import get_answer_sheet as sheets
from modules.results.services.queries import get_dashboard as dashboard
from modules.results.services.queries import get_gradebook as gradebook
from modules.results.services.queries import get_my_result as mine
from modules.results.services.queries import get_question_stats as questions
from modules.results.services.queries import list_my_past_tests as past
from modules.results.services.queries import list_results_inbox as inbox


def get_gradebook(request: HttpRequest, assignment_id: UUID) -> GradebookOut:
    return GradebookOut.from_book(
        gradebook.get_gradebook(ctx_from(request), assignment_id=assignment_id)
    )


def get_question_stats(request: HttpRequest, assignment_id: UUID) -> list[QuestionStatOut]:
    found = questions.get_question_stats(ctx_from(request), assignment_id=assignment_id)
    return [QuestionStatOut.from_view(v) for v in found]


def get_answer_key(request: HttpRequest, assignment_id: UUID) -> KeyedPaperOut:
    return KeyedPaperOut.from_keyed(
        keys.get_answer_key_view(ctx_from(request), assignment_id=assignment_id)
    )


def get_answer_sheet(request: HttpRequest, attempt_id: UUID) -> AnswerSheetOut:
    return AnswerSheetOut.from_sheet(
        sheets.get_answer_sheet(ctx_from(request), attempt_id=attempt_id)
    )


def list_answer_sheets(
    request: HttpRequest, assignment_id: UUID, query: Query[SheetsIn]
) -> list[AnswerSheetOut]:
    found = sheets.list_answer_sheets(
        ctx_from(request), assignment_id=assignment_id, attempt_ids=query.ids()
    )
    return [AnswerSheetOut.from_sheet(s) for s in found]


def export_gradebook_csv(request: HttpRequest, assignment_id: UUID) -> HttpResponse:
    file = exporting.export_gradebook_csv(ctx_from(request), assignment_id=assignment_id)
    response = HttpResponse(file.text, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(file.name)}"
    return response


def list_results_inbox(
    request: HttpRequest, query: Query[InboxIn], page: Query[PageIn]
) -> Page[ResultsInboxRowOut]:
    rows = inbox.list_results_inbox(ctx_from(request), tab=query.tab)
    shown = [ResultsInboxRowOut.from_inbox(r) for r in rows[page.offset : page.offset + page.limit]]
    return Page[ResultsInboxRowOut].of(shown, page=page, total=len(rows))


def get_dashboard(request: HttpRequest) -> DashboardOut:
    return DashboardOut.from_dashboard(dashboard.get_dashboard(ctx_from(request)))


def list_my_past_tests(request: HttpRequest, page: Query[PageIn]) -> Page[PastTestOut]:
    cards = past.list_my_past_tests(ctx_from(request))
    shown = [PastTestOut.from_card(c) for c in cards[page.offset : page.offset + page.limit]]
    return Page[PastTestOut].of(shown, page=page, total=len(cards))


def get_my_result(request: HttpRequest, attempt_id: UUID) -> ResultOut:
    found = mine.get_my_result(ctx_from(request), attempt_id=attempt_id)
    return ResultOut.from_view(found.result, score_hidden=found.score_hidden)
