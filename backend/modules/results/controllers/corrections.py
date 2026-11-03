from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.results.dto.corrections import KeyCorrectedOut, KeyCorrectionIn
from modules.results.services.commands import correct_answer_key as correcting


def correct_answer_key(
    request: HttpRequest, assignment_id: UUID, payload: KeyCorrectionIn
) -> KeyCorrectedOut:
    result = correcting.correct_answer_key(
        ctx_from(request),
        assignment_id=assignment_id,
        question_id=payload.question_id,
        entry=payload.entry.to_entry(),
        reason=payload.reason,
    )
    return KeyCorrectedOut.from_result(result)
