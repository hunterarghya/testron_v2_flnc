"""Every authoring endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea

router = Router(tags=["authoring"], auth=TeacherArea())
