"""HTTP contract of the test editor (api_contract.md §2.5, §3.2)."""

import pytest
from django.test import Client

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
TESTS = "/api/v1/admin/tests"
WORDS = {
    "v": 1,
    "type": "doc",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Which organelle?"}]}],
}


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


@pytest.fixture
def document(teacher: Client) -> dict[str, object]:
    response = send(teacher, "post", TESTS)
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def first_section(document: dict[str, object]) -> str:
    return str(document["sections"][0]["id"])  # type: ignore[index]


def test_a_new_test_has_defaults_and_one_problem(document: dict[str, object]) -> None:
    assert document["settings"] == {
        "timing": {"kind": "TOTAL", "duration_s": 3600},
        "shuffle_questions": False,
        "shuffle_options": False,
        "marking": {"marks": "4.00", "negative_marks": "1.00"},
        "integrity": {"grace_s": 5, "max_warnings": 3, "action": "AUTO_SUBMIT"},
    }
    assert document["totals"] == {"questions": 0, "marks": "0", "duration_s": 3600}
    assert document["problems"] == [
        {
            "code": "test_empty",
            "message": "The test has no questions yet.",
            "section_id": None,
            "question_id": None,
        }
    ]


def test_a_stale_revision_is_409_with_the_current_one(
    teacher: Client, document: dict[str, object]
) -> None:
    url = f"{TESTS}/{document['id']}"
    assert (
        send(teacher, "patch", url, {"revision": 1, "title": "Cell Biology"}).json()["revision"]
        == 2
    )

    stale = send(teacher, "patch", url, {"revision": 1, "title": "Genetics"})

    assert (stale.status_code, stale.json()["code"], stale.json()["context"]) == (
        409,
        "test_changed_elsewhere",
        {"revision": 2},
    )


def test_add_then_save_a_question(teacher: Client, document: dict[str, object]) -> None:
    added = send(
        teacher,
        "post",
        f"{TESTS}/{document['id']}/questions",
        {"revision": 1, "section_id": first_section(document), "type": "MCQ"},
    ).json()
    question = added["question"]
    options = [
        {"id": o["id"], "content": WORDS, "is_correct": i == 0}
        for i, o in enumerate(question["options"][:2])
    ]

    saved = send(
        teacher,
        "patch",
        f"/api/v1/admin/questions/{question['id']}",
        {
            "revision": added["revision"],
            "stem": WORDS,
            "options": options,
            "marks_override": "2.5",
            "chapter_tags": ["Cell"],
        },
    ).json()

    assert saved["problems"] == []
    assert saved["totals"]["marks"] == "2.50"
    assert saved["question"]["marks_override"] == "2.50"
    assert [t["name"] for t in saved["question"]["chapter_tags"]] == ["Cell"]
    assert [o["id"] for o in saved["question"]["options"]] == [o["id"] for o in options]


def test_rich_content_outside_the_allow_list_is_a_field_error(
    teacher: Client, document: dict[str, object]
) -> None:
    response = send(
        teacher,
        "patch",
        f"{TESTS}/{document['id']}",
        {"revision": 1, "instructions": {"v": 1, "type": "doc", "content": [{"type": "script"}]}},
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "rich_content_invalid"


def test_switching_to_sectioned_then_adding_a_section(
    teacher: Client, document: dict[str, object]
) -> None:
    url = f"{TESTS}/{document['id']}"
    switched = send(
        teacher, "patch", url, {"revision": 1, "settings": {"timing": {"kind": "SECTIONED"}}}
    ).json()

    added = send(
        teacher,
        "post",
        f"{url}/sections",
        {
            "revision": switched["revision"],
            "after_section_id": first_section(document),
            "title": "Botany",
            "duration_s": 600,
        },
    ).json()

    assert added["section"]["title"] == "Botany"
    assert added["totals"]["duration_s"] == 4200


def test_delete_a_question_with_the_revision_in_the_query(
    teacher: Client, document: dict[str, object]
) -> None:
    added = send(
        teacher,
        "post",
        f"{TESTS}/{document['id']}/questions",
        {"revision": 1, "section_id": first_section(document), "type": "NUMERICAL"},
    ).json()

    deleted = teacher.delete(
        f"/api/v1/admin/questions/{added['question']['id']}?revision={added['revision']}"
    )

    assert deleted.json()["totals"]["questions"] == 0


def test_a_structure_that_misses_a_section_is_422(
    teacher: Client, document: dict[str, object]
) -> None:
    response = send(
        teacher, "put", f"{TESTS}/{document['id']}/structure", {"revision": 1, "sections": []}
    )

    assert response.status_code == 422
