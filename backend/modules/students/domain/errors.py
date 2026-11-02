from core.errors import Conflict


class AdmissionStepNotAllowed(Conflict):
    """The student isn't in the status this step starts from."""

    code = "admission_step_not_allowed"
    title = "This account can't take that step now"
