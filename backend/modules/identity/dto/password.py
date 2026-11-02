from ninja import Schema
from pydantic import ConfigDict, Field

from core.http.fields import EmailField, PasswordField


class PasswordResetIn(Schema):
    model_config = ConfigDict(extra="forbid")

    email: EmailField


class PasswordResetConfirmIn(Schema):
    model_config = ConfigDict(extra="forbid")

    email: EmailField
    # Optional in shape only: a missing code is refused as otp_invalid (V1 F-01)
    code: str = Field(default="", max_length=12)
    new_password: PasswordField


class ChangePasswordIn(Schema):
    model_config = ConfigDict(extra="forbid")

    # Left out when a Google-only account sets its first password
    current_password: PasswordField | None = None
    new_password: PasswordField
