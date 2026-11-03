from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Status

from core.http.bulk import BulkResultOut
from core.http.context import ctx_from
from core.http.pagination import Page, PageIn
from modules.assignments.dto.requests import (
    AssignmentFilterIn,
    AudienceIn,
    CreateAssignmentIn,
    PasswordIn,
    ReplaceAudienceIn,
    UpdateAssignmentIn,
)
from modules.assignments.dto.views import AssignmentDetailOut, AssignmentRowOut, PasswordOut
from modules.assignments.services.commands import add_audience as adding
from modules.assignments.services.commands import cancel_assignment as cancelling
from modules.assignments.services.commands import create_assignment as creating
from modules.assignments.services.commands import remove_audience as removing
from modules.assignments.services.commands import replace_audience as replacing
from modules.assignments.services.commands import set_password as passwords
from modules.assignments.services.commands import update_assignment as updating
from modules.assignments.services.queries import get_assignment as detail
from modules.assignments.services.queries import list_assignments as listing
from modules.assignments.services.queries import reveal_password as revealing


def list_assignments(
    request: HttpRequest, filters: Query[AssignmentFilterIn], page: Query[PageIn]
) -> Page[AssignmentRowOut]:
    result = listing.list_assignments(
        ctx_from(request), filters=filters.to_filter(), offset=page.offset, limit=page.limit
    )
    rows = [AssignmentRowOut.from_row(row) for row in result.rows]
    return Page[AssignmentRowOut].of(rows, page=page, total=result.total)


def create_assignment(
    request: HttpRequest, payload: CreateAssignmentIn
) -> Status[AssignmentDetailOut]:
    created = creating.create_assignment(ctx_from(request), new=payload.to_new())
    return Status(201, AssignmentDetailOut.from_detail(created))


def get_assignment(request: HttpRequest, assignment_id: UUID) -> AssignmentDetailOut:
    found = detail.get_assignment(ctx_from(request), assignment_id=assignment_id)
    return AssignmentDetailOut.from_detail(found)


def update_assignment(
    request: HttpRequest, assignment_id: UUID, payload: UpdateAssignmentIn
) -> AssignmentDetailOut:
    updated = updating.update_assignment(
        ctx_from(request), assignment_id=assignment_id, patch=payload.to_patch()
    )
    return AssignmentDetailOut.from_detail(updated)


def replace_audience(
    request: HttpRequest, assignment_id: UUID, payload: ReplaceAudienceIn
) -> AssignmentDetailOut:
    updated = replacing.replace_audience(
        ctx_from(request),
        assignment_id=assignment_id,
        student_ids=payload.student_ids,
        source_group_ids=payload.source_group_ids,
    )
    return AssignmentDetailOut.from_detail(updated)


def add_audience(request: HttpRequest, assignment_id: UUID, payload: AudienceIn) -> BulkResultOut:
    outcome = adding.add_audience(
        ctx_from(request), assignment_id=assignment_id, student_ids=payload.student_ids
    )
    return BulkResultOut.from_outcome(outcome)


def remove_audience(
    request: HttpRequest, assignment_id: UUID, payload: AudienceIn
) -> BulkResultOut:
    outcome = removing.remove_audience(
        ctx_from(request), assignment_id=assignment_id, student_ids=payload.student_ids
    )
    return BulkResultOut.from_outcome(outcome)


def set_password(request: HttpRequest, assignment_id: UUID, payload: PasswordIn) -> Status[None]:
    passwords.set_password(
        ctx_from(request),
        assignment_id=assignment_id,
        password=payload.password,
        password_confirm=payload.password_confirm,
    )
    return Status(204, None)


def reveal_password(request: HttpRequest, assignment_id: UUID) -> PasswordOut:
    password = revealing.reveal_password(ctx_from(request), assignment_id=assignment_id)
    return PasswordOut(password=password)


def cancel_assignment(request: HttpRequest, assignment_id: UUID) -> Status[None]:
    cancelling.cancel_assignment(ctx_from(request), assignment_id=assignment_id)
    return Status(204, None)
