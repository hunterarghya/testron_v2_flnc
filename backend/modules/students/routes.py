"""Every students endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea

router = Router(tags=["students"], auth=TeacherArea())
