"""Every delivery endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import StudentArea

# Student area by default; the teacher monitor routes set auth=TeacherArea()
router = Router(tags=["delivery"], auth=StudentArea())
