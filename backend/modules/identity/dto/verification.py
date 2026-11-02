from ninja import Schema
from pydantic import ConfigDict

from core.http.fields import EmailField


class ResendVerificationIn(Schema):
    model_config = ConfigDict(extra="forbid")

    email: EmailField
