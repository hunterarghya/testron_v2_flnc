from core.errors import DomainError, Invalid


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
