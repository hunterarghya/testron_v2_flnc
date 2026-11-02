"""The one error hierarchy every layer raises (architecture.md §5.4).

Each error declares its stable `code`, HTTP `status` and `title` once. The global
handler in `core.http.problems` turns any of them into problem+json, so no other
layer knows about HTTP. Plain Python only: domain code may import this.
"""

from collections.abc import Mapping
from typing import ClassVar


class DomainError(Exception):
    code: ClassVar[str] = "domain_error"
    status: ClassVar[int] = 400
    title: ClassVar[str] = "The request could not be completed"

    def __init__(self, detail: str | None = None, *, context: Mapping[str, object] | None = None):
        super().__init__(detail or self.title)
        self.detail = detail
        self.context = dict(context or {})


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


class Invalid(DomainError):
    code = "invalid"
    status = 422
    title = "The request is not valid"
