from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import ConfigDict

from modules.identity.services.queries.get_health import HealthView


class HealthOut(Schema):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    server_now: datetime
    version: str
    commit: str

    @classmethod
    def from_view(cls, view: HealthView) -> "HealthOut":
        return cls(
            status="ok", server_now=view.server_now, version=view.version, commit=view.commit
        )
