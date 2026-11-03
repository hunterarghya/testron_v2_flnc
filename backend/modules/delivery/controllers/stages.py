from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.delivery.controllers.attempts import exam_client
from modules.delivery.dto.attempt_clock import NextStageIn
from modules.delivery.dto.attempt_state import AttemptStateOut
from modules.delivery.services.commands import move_to_next_stage as moving
from modules.delivery.services.commands import return_to_stage as returning


def move_to_next_stage(
    request: HttpRequest, attempt_id: UUID, payload: NextStageIn
) -> AttemptStateOut:
    view = moving.move_to_next_stage(
        ctx_from(request),
        attempt_id=attempt_id,
        from_stage_index=payload.from_stage_index,
        client_id=exam_client(request),
    )
    return AttemptStateOut.from_state(view)


def return_to_stage(request: HttpRequest, attempt_id: UUID, stage_index: int) -> AttemptStateOut:
    # Any number may arrive here; the domain refuses one that isn't a stage to go back to
    view = returning.return_to_stage(
        ctx_from(request),
        attempt_id=attempt_id,
        stage_index=stage_index,
        client_id=exam_client(request),
    )
    return AttemptStateOut.from_state(view)
