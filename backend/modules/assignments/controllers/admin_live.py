from uuid import UUID

from django.http import HttpRequest

from core.http.bulk import BulkResultOut
from core.http.context import ctx_from
from modules.assignments.dto.lobby import ExtendedOut, ExtendTimeIn
from modules.assignments.dto.requests import AudienceIn
from modules.assignments.services.commands import extend_time as extending
from modules.assignments.services.commands import grant_retakes as granting


def extend_time(request: HttpRequest, assignment_id: UUID, payload: ExtendTimeIn) -> ExtendedOut:
    ends_at = extending.extend_time(
        ctx_from(request),
        assignment_id=assignment_id,
        seconds=payload.seconds,
        student_ids=payload.student_ids,
        stage_index=payload.stage_index,
    )
    return ExtendedOut(ends_at=ends_at)


def grant_retakes(request: HttpRequest, assignment_id: UUID, payload: AudienceIn) -> BulkResultOut:
    outcome = granting.grant_retakes(
        ctx_from(request), assignment_id=assignment_id, student_ids=payload.student_ids
    )
    return BulkResultOut.from_outcome(outcome)
