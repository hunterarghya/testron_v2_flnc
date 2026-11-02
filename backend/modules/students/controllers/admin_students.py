from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Status

from core.context import StudentStatus
from core.http.context import ctx_from
from core.http.pagination import Page, PageIn
from modules.students.dto.students import (
    AnonymizeIn,
    BulkResultOut,
    StudentFilterIn,
    StudentIdsIn,
    StudentRowOut,
)
from modules.students.services.commands import anonymize_student as anonymize
from modules.students.services.commands import approve_students as approve
from modules.students.services.commands import deactivate_students as deactivate
from modules.students.services.commands import decline_students as decline
from modules.students.services.commands import reactivate_students as reactivate
from modules.students.services.queries import list_students as listing


def list_students(
    request: HttpRequest, filters: Query[StudentFilterIn], page: Query[PageIn]
) -> Page[StudentRowOut]:
    result = listing.list_students(
        ctx_from(request),
        status=StudentStatus(filters.status),
        search=filters.q,
        offset=page.offset,
        limit=page.limit,
    )
    rows = [StudentRowOut.from_row(row) for row in result.rows]
    return Page[StudentRowOut].of(rows, page=page, total=result.total)


def approve_students(request: HttpRequest, payload: StudentIdsIn) -> BulkResultOut:
    outcome = approve.approve_students(ctx_from(request), student_ids=payload.student_ids)
    return BulkResultOut.from_outcome(outcome)


def decline_students(request: HttpRequest, payload: StudentIdsIn) -> BulkResultOut:
    outcome = decline.decline_students(ctx_from(request), student_ids=payload.student_ids)
    return BulkResultOut.from_outcome(outcome)


def deactivate_students(request: HttpRequest, payload: StudentIdsIn) -> BulkResultOut:
    outcome = deactivate.deactivate_students(ctx_from(request), student_ids=payload.student_ids)
    return BulkResultOut.from_outcome(outcome)


def reactivate_students(request: HttpRequest, payload: StudentIdsIn) -> BulkResultOut:
    outcome = reactivate.reactivate_students(ctx_from(request), student_ids=payload.student_ids)
    return BulkResultOut.from_outcome(outcome)


def anonymize_student(request: HttpRequest, student_id: UUID, payload: AnonymizeIn) -> Status[None]:
    anonymize.anonymize_student(
        ctx_from(request), student_id=student_id, confirm_name=payload.confirm_name
    )
    return Status(204, None)
