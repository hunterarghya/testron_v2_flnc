"""Every API operation, read from the generated OpenAPI document, with the area it belongs to
(security.md §3.1). The area tables below are the expectations: a new route fails the
security suite until it is listed here."""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from config.api import api


class Area(StrEnum):
    PUBLIC = "public"  # anyone
    SIGNED_IN = "signed_in"  # any logged-in person, whatever their status
    TEACHER = "teacher"  # /admin/**
    STUDENT = "student"  # /my/** and /attempts/**: ACTIVE students only


# Routes outside the prefix areas, one by one
ROUTE_AREAS: dict[str, Area] = {
    "GET /api/v1/healthz": Area.PUBLIC,
    "GET /api/v1/auth/csrf": Area.PUBLIC,
    "GET /api/v1/auth/session": Area.PUBLIC,
    "POST /api/v1/auth/sign-up": Area.PUBLIC,
    "POST /api/v1/auth/email-verification": Area.PUBLIC,
    "POST /api/v1/auth/email-verification/resend": Area.PUBLIC,
    "POST /api/v1/auth/login": Area.PUBLIC,
    "POST /api/v1/auth/password-reset": Area.PUBLIC,
    "POST /api/v1/auth/password-reset/confirm": Area.PUBLIC,
    "POST /api/v1/auth/logout": Area.SIGNED_IN,
    "POST /api/v1/auth/password": Area.SIGNED_IN,
    "PATCH /api/v1/auth/profile": Area.SIGNED_IN,
}
PREFIX_AREAS: tuple[tuple[str, Area], ...] = (
    ("/api/v1/admin/", Area.TEACHER),
    ("/api/v1/my/", Area.STUDENT),
    ("/api/v1/attempts/", Area.STUDENT),
)
_PATH_PARAMETER = re.compile(r"\{[^}]+\}")
_UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass(frozen=True, slots=True)
class Operation:
    method: str
    path: str

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"

    @property
    def is_unsafe(self) -> bool:
        return self.method in _UNSAFE

    def url(self) -> str:
        """The path with every `{parameter}` filled by a fresh id."""
        return _PATH_PARAMETER.sub(lambda _: str(uuid4()), self.path)


def all_operations() -> list[Operation]:
    paths = api.get_openapi_schema()["paths"]
    return [Operation(method.upper(), path) for path, item in paths.items() for method in item]


def area_of(operation: Operation) -> Area | None:
    if operation.key in ROUTE_AREAS:
        return ROUTE_AREAS[operation.key]
    return next((area for prefix, area in PREFIX_AREAS if operation.path.startswith(prefix)), None)
