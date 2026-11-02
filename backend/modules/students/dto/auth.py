from typing import Literal, cast
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from core.http.fields import EmailField, NameField, PasswordField
from modules.students.services.commands.sign_up_with_password import SignUpResult
from modules.students.services.session_user import SessionUserView

StatusOut = Literal["UNVERIFIED", "PENDING", "ACTIVE", "DECLINED", "DEACTIVATED"]


class SignUpIn(Schema):
    model_config = ConfigDict(extra="forbid")

    name: NameField
    email: EmailField
    password: PasswordField


class SignUpAcceptedOut(Schema):
    model_config = ConfigDict(extra="forbid")

    email_masked: str

    @classmethod
    def from_result(cls, result: SignUpResult) -> "SignUpAcceptedOut":
        return cls(email_masked=result.email_masked)


class VerifyEmailIn(Schema):
    model_config = ConfigDict(extra="forbid")

    email: EmailField
    # Optional in shape only: a missing code is refused as otp_invalid (V1 F-01)
    code: str = Field(default="", max_length=12)


class SessionUserOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    email: str
    role: Literal["TEACHER", "STUDENT"]
    status: StatusOut | None
    has_password: bool
    performance_shared: bool

    @classmethod
    def from_view(cls, view: SessionUserView) -> "SessionUserOut":
        return cls(
            id=view.id,
            name=view.name,
            email=view.email,
            role=view.role.value,
            # Anonymized students can't log in, so the status is always one of StatusOut
            status=cast(StatusOut, view.status.value) if view.status else None,
            has_password=view.has_password,
            performance_shared=view.performance_shared,
        )
