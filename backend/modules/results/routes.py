"""Every results endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from modules.results.controllers import badges
from modules.results.dto.badges import BadgesOut

# Teacher area by default; the student /my/* routes set auth=StudentArea()
router = Router(tags=["results"], auth=TeacherArea())

router.add_api_operation(
    "/admin/badges",
    ["GET"],
    badges.get_badges,
    response={200: BadgesOut},
    summary="The counts on the teacher's menu",
)
