"""Query parameters of the results endpoints (api_contract.md §2.7)."""

from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field, field_validator

from modules.results.services.queries.list_results_inbox import InboxTab


class InboxIn(Schema):
    model_config = ConfigDict(extra="forbid")
    tab: InboxTab = InboxTab.TO_PUBLISH


class SheetsIn(Schema):
    model_config = ConfigDict(extra="forbid")
    # Comma-separated; absent = every ended attempt
    attempt_ids: str | None = Field(default=None, max_length=40_000)

    @field_validator("attempt_ids")
    @classmethod
    def _uuids(cls, raw: str | None) -> str | None:
        for part in (raw or "").split(","):
            if part:
                UUID(part)  # a ValueError here is a 422 on attempt_ids
        return raw

    def ids(self) -> list[UUID] | None:
        return None if not self.attempt_ids else [UUID(i) for i in self.attempt_ids.split(",") if i]
