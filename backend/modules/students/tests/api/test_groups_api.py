"""HTTP contract of groups, the audience preview and sharing (api_contract.md §2.3, §2.6)."""

import pytest
from django.test import Client

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
GROUPS = "/api/v1/admin/groups"


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def create(client: Client, name: str) -> dict[str, object]:
    response = send(client, "post", GROUPS, {"name": name})
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def test_create_answers_201_with_the_group(teacher: Client) -> None:
    group = create(teacher, "  Class 11 A ")

    assert (group["name"], group["description"], group["member_count"]) == ("Class 11 A", "", 0)
    assert group["archived_at"] is None


def test_a_taken_name_is_a_field_error(teacher: Client) -> None:
    create(teacher, "Class 11 A")

    response = send(teacher, "post", GROUPS, {"name": "class 11 a"})

    assert (response.status_code, response.json()["code"]) == (422, "validation_error")
    assert response.json()["errors"][0]["field"] == "name"
    assert response.json()["errors"][0]["code"] == "taken"


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
def test_bad_names_are_refused(teacher: Client, name: str) -> None:
    assert send(teacher, "post", GROUPS, {"name": name}).status_code == 422


def test_group_detail_and_members(teacher: Client) -> None:
    group = create(teacher, "Class 11 A")
    student = make_student(name="Aditi Roy")
    added = send(
        teacher, "post", f"{GROUPS}/{group['id']}/members", {"student_ids": [str(student.id)]}
    )

    detail = teacher.get(f"{GROUPS}/{group['id']}").json()

    assert added.json()["succeeded"] == [str(student.id)]
    assert detail["group"]["member_count"] == 1
    assert [member["name"] for member in detail["members"]] == ["Aditi Roy"]


def test_archived_group_member_change_is_409(teacher: Client) -> None:
    group = create(teacher, "Class 11 A")
    send(teacher, "post", f"{GROUPS}/{group['id']}/archive")

    response = send(
        teacher,
        "post",
        f"{GROUPS}/{group['id']}/members",
        {"student_ids": [str(make_student().id)]},
    )

    assert (response.status_code, response.json()["code"]) == (409, "group_archived")


def test_audience_preview_takes_comma_separated_groups(teacher: Client) -> None:
    eleven, twelve = create(teacher, "11 A"), create(teacher, "12 B")
    student = make_student(name="Aditi")
    for group in (eleven, twelve):
        send(teacher, "post", f"{GROUPS}/{group['id']}/members", {"student_ids": [str(student.id)]})

    preview = teacher.get(
        "/api/v1/admin/audience-preview", {"group_ids": f"{eleven['id']},{twelve['id']}"}
    ).json()

    assert [(row["name"], sorted(row["group_names"])) for row in preview] == [
        ("Aditi", ["11 A", "12 B"])
    ]


def test_students_list_filters_by_group_and_names_the_groups(teacher: Client) -> None:
    group = create(teacher, "11 A")
    member, other = make_student(name="Aditi"), make_student(name="Tapas")
    send(teacher, "post", f"{GROUPS}/{group['id']}/members", {"student_ids": [str(member.id)]})

    rows = teacher.get("/api/v1/admin/students", {"group_id": str(group["id"])}).json()["items"]

    assert [(row["name"], row["group_names"]) for row in rows] == [("Aditi", ["11 A"])]
    assert other.id


@pytest.mark.parametrize(
    "body",
    [
        {},
        {
            "student_ids": ["00000000-0000-0000-0000-000000000001"],
            "group_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
)
def test_share_needs_exactly_one_target(teacher: Client, body: dict[str, object]) -> None:
    assert send(teacher, "post", "/api/v1/admin/performance-shares", body).status_code == 422


def test_share_and_unshare_show_on_the_students_list(teacher: Client) -> None:
    student = make_student()
    send(teacher, "post", "/api/v1/admin/performance-shares", {"student_ids": [str(student.id)]})

    shared = teacher.get("/api/v1/admin/students").json()["items"][0]["performance_shared"]
    send(
        teacher,
        "post",
        "/api/v1/admin/performance-shares/remove",
        {"student_ids": [str(student.id)]},
    )
    unshared = teacher.get("/api/v1/admin/students").json()["items"][0]["performance_shared"]

    assert (shared, unshared) == (True, False)
