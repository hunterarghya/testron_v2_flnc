"""Page-number pagination for list endpoints (ADR-024, api_contract.md §0)."""

from ninja import Schema
from pydantic import ConfigDict, Field

MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50


class PageIn(Schema):
    """`?page=1&page_size=50`, taken by list controllers with `Query[PageIn]`."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page[ItemOut](Schema):
    """`{items, page, page_size, total}`: tables need the total to show page counts."""

    items: list[ItemOut]
    page: int
    page_size: int
    total: int

    @classmethod
    def of(cls, items: list[ItemOut], *, page: PageIn, total: int) -> "Page[ItemOut]":
        return cls(items=items, page=page.page, page_size=page.page_size, total=total)
