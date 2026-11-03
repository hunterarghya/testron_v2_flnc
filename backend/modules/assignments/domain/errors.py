from collections.abc import Collection
from uuid import UUID

from core.errors import Conflict


class AssignmentStarted(Conflict):
    """Only some things can change once the test has started (domain_model.md §3.5 #5)."""

    code = "assignment_started"
    title = "This can't change after the test has started"

    def __init__(self, editable_fields: Collection[str]) -> None:
        super().__init__(context={"editable_fields": list(editable_fields)})


class AssignmentCancelled(Conflict):
    """A cancelled assignment is read-only (domain_model.md §3.5 #6)."""

    code = "assignment_cancelled"
    title = "This assignment was cancelled"


class AssignmentHasAttempts(Conflict):
    """Cancel only while no one has started (domain_model.md §3.5 #6)."""

    code = "assignment_has_attempts"
    title = "Students have already started this test"


class AudienceMemberHasAttempt(Conflict):
    """A student who has started stays in the audience (E-11)."""

    code = "audience_member_has_attempt"
    title = "These students have already started"

    def __init__(self, student_ids: Collection[UUID]) -> None:
        super().__init__(context={"student_ids": sorted(str(sid) for sid in student_ids)})
