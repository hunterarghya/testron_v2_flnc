"""Every results endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea

# Teacher area by default; the student /my/* routes set auth=StudentArea()
router = Router(tags=["results"], auth=TeacherArea())
