"""HTTP contract of the tag endpoints (api_contract.md §2.4)."""

import pytest
from django.test import Client

from conftest import MakeCtx
from core.clock import FrozenClock
from modules.tagging.public import TagKind, ensure_tags_by_name
from tests.clients import logged_in, send
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
TAGS = "/api/v1/admin/tags"


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def test_suggest_answers_tags(teacher: Client, make_ctx: MakeCtx) -> None:
    ensure_tags_by_name(make_ctx(), kind=TagKind.CHAPTER, names=["Cell", "Nucleus"])

    body = teacher.get(f"{TAGS}/suggest", {"kind": "CHAPTER", "q": "ce"}).json()

    assert [(tag["kind"], tag["name"]) for tag in body] == [("CHAPTER", "Cell")]


def test_suggest_needs_a_kind(teacher: Client) -> None:
    assert teacher.get(f"{TAGS}/suggest", {"q": "ce"}).status_code == 422


def test_list_has_usage_counts(teacher: Client, make_ctx: MakeCtx) -> None:
    ensure_tags_by_name(make_ctx(), kind=TagKind.TOPIC, names=["Mitosis"])

    body = teacher.get(TAGS).json()

    assert body == [
        {
            "id": body[0]["id"],
            "kind": "TOPIC",
            "name": "Mitosis",
            "question_count": 0,
            "test_count": 0,
        }
    ]


def test_rename_onto_another_tag_is_409_until_merge_is_confirmed(
    teacher: Client, make_ctx: MakeCtx
) -> None:
    typo, real = ensure_tags_by_name(
        make_ctx(), kind=TagKind.CHAPTER, names=["Genetcs", "Genetics"]
    )

    refused = send(teacher, "patch", f"{TAGS}/{typo.id}", {"name": "Genetics"})
    merged = send(teacher, "patch", f"{TAGS}/{typo.id}", {"name": "Genetics", "merge": True})

    assert (refused.status_code, refused.json()["code"]) == (409, "tag_exists")
    assert refused.json()["context"]["target"]["name"] == "Genetics"
    assert merged.json() == {
        "tag": {"id": str(real.id), "kind": "CHAPTER", "name": "Genetics"},
        "merged_from": str(typo.id),
    }


def test_blank_name_is_a_field_error(teacher: Client, make_ctx: MakeCtx) -> None:
    tag = ensure_tags_by_name(make_ctx(), kind=TagKind.CHAPTER, names=["Cell"])[0]

    response = send(teacher, "patch", f"{TAGS}/{tag.id}", {"name": "  "})

    assert response.json()["errors"][0]["field"] == "name"


def test_delete_reports_how_many_questions_lost_the_tag(teacher: Client, make_ctx: MakeCtx) -> None:
    tag = ensure_tags_by_name(make_ctx(), kind=TagKind.CHAPTER, names=["Cell"])[0]

    response = send(teacher, "delete", f"{TAGS}/{tag.id}")

    assert response.json() == {"removed_from_questions": 0}
    assert teacher.get(TAGS).json() == []
