from uuid import UUID

from django.http import HttpRequest
from ninja import Status

from core.http.context import ctx_from
from modules.delivery.dto.attempt_clock import (
    AttemptClockOut,
    SaveAckOut,
    SaveResponseIn,
    StartAttemptIn,
    SubmitResultOut,
)
from modules.delivery.dto.attempt_state import AttemptStateOut
from modules.delivery.services.commands import record_visit as visiting
from modules.delivery.services.commands import save_response as saving
from modules.delivery.services.commands import start_attempt as starting
from modules.delivery.services.commands import submit_attempt as submitting
from modules.delivery.services.queries import get_attempt_clock as heartbeat
from modules.delivery.services.queries import get_attempt_state as state

# The exam client that may write: the latest device wins (api_contract.md §2.8)
EXAM_CLIENT_HEADER = "X-Exam-Client"


def exam_client(request: HttpRequest) -> UUID | None:
    """None when missing or malformed: either way it isn't the active client."""
    try:
        return UUID(request.headers.get(EXAM_CLIENT_HEADER, ""))
    except ValueError:
        return None


def start_attempt(
    request: HttpRequest, assignment_id: UUID, payload: StartAttemptIn
) -> Status[AttemptStateOut]:
    started = starting.start_attempt(
        ctx_from(request),
        assignment_id=assignment_id,
        password=payload.password,
        client_id=exam_client(request),
    )
    return Status(201 if started.created else 200, AttemptStateOut.from_state(started.view))


def get_attempt_state(request: HttpRequest, attempt_id: UUID) -> AttemptStateOut:
    view = state.get_attempt_state(
        ctx_from(request), attempt_id=attempt_id, client_id=exam_client(request)
    )
    return AttemptStateOut.from_state(view)


def save_response(
    request: HttpRequest, attempt_id: UUID, question_id: UUID, payload: SaveResponseIn
) -> SaveAckOut:
    saved = saving.save_response(
        ctx_from(request),
        attempt_id=attempt_id,
        client_id=exam_client(request),
        save=payload.to_request(question_id),
    )
    return SaveAckOut.from_saved(saved)


def record_visit(request: HttpRequest, attempt_id: UUID, question_id: UUID) -> Status[None]:
    visiting.record_visit(
        ctx_from(request),
        attempt_id=attempt_id,
        question_id=question_id,
        client_id=exam_client(request),
    )
    return Status(204, None)


def heartbeat_attempt(request: HttpRequest, attempt_id: UUID) -> AttemptClockOut:
    view = heartbeat.get_attempt_clock(
        ctx_from(request), attempt_id=attempt_id, client_id=exam_client(request)
    )
    return AttemptClockOut.from_view(view)


def submit_attempt(request: HttpRequest, attempt_id: UUID) -> SubmitResultOut:
    ending = submitting.submit_attempt(
        ctx_from(request), attempt_id=attempt_id, client_id=exam_client(request)
    )
    return SubmitResultOut.from_ending(ending)
