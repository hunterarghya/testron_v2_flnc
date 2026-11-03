"""The one error hierarchy every layer raises (architecture.md §5.4).

Each error declares its stable `code`, HTTP `status` and `title` once. The global
handler in `core.http.problems` turns any of them into problem+json, so no other
layer knows about HTTP. Plain Python only: domain code may import this.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class FieldError:
    """One invalid field, shaped like a request-validation error (api_contract.md §1)."""

    field: str
    code: str
    message: str


class DomainError(Exception):
    code: ClassVar[str] = "domain_error"
    status: ClassVar[int] = 400
    title: ClassVar[str] = "The request could not be completed"

    def __init__(self, detail: str | None = None, *, context: Mapping[str, object] | None = None):
        super().__init__(detail or self.title)
        self.detail = detail
        self.context = dict(context or {})

    def response_headers(self) -> dict[str, str]:
        """Extra HTTP headers the problem response carries (most errors have none)."""
        return {}

    def field_errors(self) -> Sequence[FieldError]:
        """Per-field problems, listed as `errors[]` like a request-validation error."""
        return ()


class NotAuthenticated(DomainError):
    code = "not_authenticated"
    status = 401
    title = "Please log in"


class Forbidden(DomainError):
    code = "forbidden"
    status = 403
    title = "You can't do this"


class AccountNotActive(DomainError):
    """A student who isn't ACTIVE (yet, or any more) calls a student endpoint."""

    code = "account_not_active"
    status = 403
    title = "Your account isn't active"


class NotFound(DomainError):
    """Missing, or not the caller's. Both look the same, so existence never leaks."""

    code = "not_found"
    status = 404
    title = "Not found"

    def __init__(self, resource: str = "item") -> None:
        super().__init__(f"The {resource} was not found.")


class Conflict(DomainError):
    code = "conflict"
    status = 409
    title = "This conflicts with the current state"


class RateLimited(DomainError):
    code = "rate_limited"
    status = 429
    title = "Too many tries"

    def __init__(self, *, retry_after_s: int) -> None:
        super().__init__(context={"retry_after_s": retry_after_s})
        self.retry_after_s = retry_after_s

    def response_headers(self) -> dict[str, str]:
        return {"Retry-After": str(self.retry_after_s)}


class Invalid(DomainError):
    code = "invalid"
    status = 422
    title = "The request is not valid"


class ConfirmationMismatch(Invalid):
    """A typed confirmation ("END", the student's name) doesn't match (api_contract.md §1)."""

    code = "confirmation_mismatch"
    title = "The confirmation text doesn't match"


class FieldsInvalid(Invalid):
    """A rule about specific fields that only the server can check (e.g. a name already taken)."""

    code = "validation_error"
    title = "Some fields are not valid"

    def __init__(self, *errors: FieldError) -> None:
        super().__init__()
        self._errors = errors

    def field_errors(self) -> Sequence[FieldError]:
        return self._errors
