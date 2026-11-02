import pytest
from pydantic import ValidationError

from core.http.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page, PageIn


def test_defaults_are_first_page_of_fifty() -> None:
    page = PageIn()

    assert (page.page, page.page_size) == (1, DEFAULT_PAGE_SIZE)
    assert (page.offset, page.limit) == (0, 50)


def test_offset_skips_earlier_pages() -> None:
    assert PageIn(page=3, page_size=20).offset == 40


@pytest.mark.parametrize(
    "values",
    [{"page": 0}, {"page_size": 0}, {"page_size": MAX_PAGE_SIZE + 1}, {"sort": "name"}],
    ids=["page-zero", "size-zero", "size-too-big", "unknown-param"],
)
def test_invalid_page_request_is_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PageIn.model_validate(values)


def test_page_carries_items_and_total() -> None:
    page = Page[str].of(["a", "b"], page=PageIn(page=2, page_size=2), total=5)

    assert page.model_dump() == {"items": ["a", "b"], "page": 2, "page_size": 2, "total": 5}
