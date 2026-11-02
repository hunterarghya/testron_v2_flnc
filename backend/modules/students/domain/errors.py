from core.errors import Conflict, Invalid


class AdmissionStepNotAllowed(Conflict):
    """The student isn't in the status this step starts from."""

    code = "admission_step_not_allowed"
    title = "This account can't take that step now"


class ConfirmationMismatch(Invalid):
    code = "confirmation_mismatch"
    title = "The confirmation text doesn't match"
