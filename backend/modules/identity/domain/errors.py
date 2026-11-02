from core.errors import Conflict, DomainError, Invalid


class DatabaseUnavailable(DomainError):
    """The deep health check couldn't reach the database."""

    code = "database_unavailable"
    status = 503
    title = "The database is not reachable"


class PasswordTooWeak(Invalid):
    code = "password_too_weak"
    title = "Choose a stronger password"


class OtpInvalid(Invalid):
    """Wrong, missing, expired, used or locked: one message for all (api_contract.md §1)."""

    code = "otp_invalid"
    title = "That code is not valid"


class EmailTaken(DomainError):
    """Two sign-ups raced for one address; the second is treated like an existing account."""

    code = "email_taken"
    status = 409
    title = "This email is already registered"


class InvalidCredentials(DomainError):
    """One answer for every failed login: unknown email, wrong password, no password set."""

    code = "invalid_credentials"
    status = 401
    title = "Email or password is incorrect"


class EmailNotVerified(DomainError):
    """Given only after the password matched, so it reveals nothing to a stranger."""

    code = "email_not_verified"
    status = 403
    title = "Please verify your email first"


class CurrentPasswordIncorrect(DomainError):
    code = "current_password_incorrect"
    status = 403
    title = "Your current password is not correct"


class TeacherEmailTaken(Conflict):
    """TEACHER_EMAIL already belongs to a student, so it can't become the teacher."""

    code = "teacher_email_taken"
    title = "This email already belongs to a student account"
