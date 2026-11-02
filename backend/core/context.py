"""Who is asking, and when: the first argument of every use case."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from core import clock
from core.request_id import new_request_id


class Role(StrEnum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class StudentStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DECLINED = "DECLINED"
    DEACTIVATED = "DEACTIVATED"
    ANONYMIZED = "ANONYMIZED"


@dataclass(frozen=True, slots=True)
class Actor:
    """The person making the request. Anonymous visitors have no user id."""

    user_id: UUID | None = None
    role: Role | None = None
    student_status: StudentStatus | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @property
    def is_teacher(self) -> bool:
        return self.is_authenticated and self.role is Role.TEACHER

    @property
    def is_active_student(self) -> bool:
        return (
            self.is_authenticated
            and self.role is Role.STUDENT
            and self.student_status is StudentStatus.ACTIVE
        )


ANONYMOUS = Actor()


@dataclass(frozen=True, slots=True)
class Ctx:
    actor: Actor
    now: datetime
    request_id: str


def system_ctx() -> Ctx:
    """The context for work no person asked for: management commands, housekeeping."""
    return Ctx(actor=ANONYMOUS, now=clock.now(), request_id=new_request_id())
