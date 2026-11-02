from core.errors import Conflict, FieldError, FieldsInvalid, Invalid


class AdmissionStepNotAllowed(Conflict):
    """The student isn't in the status this step starts from."""

    code = "admission_step_not_allowed"
    title = "This account can't take that step now"


class ConfirmationMismatch(Invalid):
    code = "confirmation_mismatch"
    title = "The confirmation text doesn't match"


class GroupNameTaken(FieldsInvalid):
    """Another active group already has this name (shown against the name field)."""

    def __init__(self) -> None:
        super().__init__(FieldError("name", "taken", "A group with this name already exists"))


class GroupArchived(Conflict):
    """Archived groups are kept as they were: restore the group to change its members."""

    code = "group_archived"
    title = "This group is archived"
