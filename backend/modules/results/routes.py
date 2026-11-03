"""Every results endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from modules.results.controllers import badges, corrections
from modules.results.dto.badges import BadgesOut
from modules.results.dto.corrections import KeyCorrectedOut

# Teacher area by default; the student /my/* routes set auth=StudentArea()
router = Router(tags=["results"], auth=TeacherArea())

router.add_api_operation(
    "/admin/badges",
    ["GET"],
    badges.get_badges,
    response={200: BadgesOut},
    summary="The counts on the teacher's menu",
)

# Teacher: answer key corrections (D-05)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/answer-key-corrections",
    ["POST"],
    corrections.correct_answer_key,
    response={200: KeyCorrectedOut},
    summary="Correct one question's answer and regrade everyone",
)
