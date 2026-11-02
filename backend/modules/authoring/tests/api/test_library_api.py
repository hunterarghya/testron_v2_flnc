"""HTTP contract of the Test Library, search, import and preview (api_contract.md §2.5)."""

import pytest
from django.test import Client

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
TESTS = "/api/v1/admin/tests"


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def new_test_with_question(client: Client) -> dict[str, str]:
    document = send(client, "post", TESTS).json()
    section_id = document["sections"][0]["id"]
    added = send(
        client,
        "post",
        f"{TESTS}/{document['id']}/questions",
        {"revision": 1, "section_id": section_id, "type": "MCQ"},
    ).json()
    return {
        "test_id": document["id"],
        "section_id": section_id,
        "question_id": added["question"]["id"],
    }


def test_the_library_lists_rows_with_problem_counts(teacher: Client) -> None:
    new_test_with_question(teacher)

    page = teacher.get(TESTS, {"sort": "title"}).json()

    assert (page["total"], page["page"]) == (1, 1)
    row = page["items"][0]
    assert (row["title"], row["question_count"], row["total_marks"], row["timing_kind"]) == (
        "Untitled test",
        1,
        "4.00",
        "TOTAL",
    )
    assert row["problem_count"] == 3


def test_duplicate_archive_and_restore(teacher: Client) -> None:
    ids = new_test_with_question(teacher)

    copy = send(teacher, "post", f"{TESTS}/{ids['test_id']}/duplicate")
    archived = send(teacher, "post", f"{TESTS}/{ids['test_id']}/archive").json()

    assert (copy.status_code, copy.json()["title"]) == (201, "Untitled test (copy)")
    assert archived["archived_at"] is not None
    assert teacher.get(TESTS, {"status": "archived"}).json()["total"] == 1
    assert send(teacher, "post", f"{TESTS}/{ids['test_id']}/restore").json()["archived_at"] is None


def test_preview_hides_answers_by_default(teacher: Client) -> None:
    ids = new_test_with_question(teacher)

    hidden = teacher.get(f"{TESTS}/{ids['test_id']}/preview").json()
    shown = teacher.get(f"{TESTS}/{ids['test_id']}/preview", {"show_answers": "true"}).json()

    assert hidden["timing"] == {"kind": "TOTAL", "allow_return": False}
    assert [o["label"] for o in hidden["questions"][0]["options"]] == ["A", "B", "C", "D"]
    assert hidden["questions"][0]["marks"] == "4.00"
    assert hidden["answers"] == []
    assert shown["answers"][0]["question_id"] == ids["question_id"]


def test_search_then_import(teacher: Client) -> None:
    source = new_test_with_question(teacher)
    target = new_test_with_question(teacher)

    found = teacher.get(
        "/api/v1/admin/questions/search", {"exclude_test_id": target["test_id"]}
    ).json()
    imported = send(
        teacher,
        "post",
        f"{TESTS}/{target['test_id']}/questions/import",
        {
            "revision": 2,
            "source_question_ids": [source["question_id"]],
            "section_id": target["section_id"],
        },
    ).json()

    assert [row["id"] for row in found["items"]] == [source["question_id"]]
    assert (imported["revision"], imported["totals"]["questions"]) == (3, 2)
    assert imported["questions"][0]["id"] != source["question_id"]
