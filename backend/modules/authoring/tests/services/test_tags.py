"""rename_tag, delete_tag, list_tags_with_usage, suggest_tags (domain_model.md §3.3, T-18)."""

from uuid import UUID, uuid4

import pytest

from conftest import MakeCtx
from core.context import Actor, Ctx, Role, StudentStatus
from core.errors import FieldsInvalid, Forbidden, NotFound
from modules.authoring.domain.errors import TagExists
from modules.authoring.services.commands.delete_tag import delete_tag
from modules.authoring.services.commands.rename_tag import rename_tag
from modules.authoring.services.queries.list_tags_with_usage import list_tags_with_usage
from modules.authoring.services.queries.suggest_tags import suggest_tags
from modules.tagging.public import TagKind, ensure_tags_by_name, list_tags
from tests.factories.authoring import make_question, make_section, make_test
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
CHAPTER = TagKind.CHAPTER


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=make_user(teacher=True).id, role=Role.TEACHER))


def new_tag(ctx: Ctx, name: str, kind: TagKind = CHAPTER) -> UUID:
    return ensure_tags_by_name(ctx, kind=kind, names=[name])[0].id


def names(kind: TagKind = CHAPTER) -> list[str]:
    return [tag.name for tag in list_tags(kind, search=None)]


def test_rename_changes_the_label(teacher_ctx: Ctx) -> None:
    tag_id = new_tag(teacher_ctx, "Genetcs")

    result = rename_tag(teacher_ctx, tag_id=tag_id, name=" Genetics ", merge=False)

    assert (result.tag.id, result.tag.name, result.merged_from) == (tag_id, "Genetics", None)


def test_renaming_to_a_new_case_of_itself_is_a_rename(teacher_ctx: Ctx) -> None:
    tag_id = new_tag(teacher_ctx, "cell")

    assert rename_tag(teacher_ctx, tag_id=tag_id, name="Cell", merge=False).tag.name == "Cell"


def test_renaming_onto_another_tag_asks_to_merge(teacher_ctx: Ctx) -> None:
    typo, real = new_tag(teacher_ctx, "Genetcs"), new_tag(teacher_ctx, "Genetics")

    with pytest.raises(TagExists) as error:
        rename_tag(teacher_ctx, tag_id=typo, name="genetics", merge=False)

    assert error.value.context == {
        "target": {"id": str(real), "name": "Genetics", "question_count": 0}
    }
    assert names() == ["Genetcs", "Genetics"]


def test_confirmed_merge_keeps_the_existing_tag(teacher_ctx: Ctx) -> None:
    typo, real = new_tag(teacher_ctx, "Genetcs"), new_tag(teacher_ctx, "Genetics")

    result = rename_tag(teacher_ctx, tag_id=typo, name="Genetics", merge=True)

    assert (result.tag.id, result.merged_from) == (real, typo)
    assert names() == ["Genetics"]


def test_merging_never_crosses_kinds(teacher_ctx: Ctx) -> None:
    chapter = new_tag(teacher_ctx, "Genetcs")
    new_tag(teacher_ctx, "Genetics", kind=TagKind.TOPIC)

    assert rename_tag(teacher_ctx, tag_id=chapter, name="Genetics", merge=False).merged_from is None


def test_bad_names_are_field_errors(teacher_ctx: Ctx) -> None:
    with pytest.raises(FieldsInvalid):
        rename_tag(teacher_ctx, tag_id=new_tag(teacher_ctx, "Cell"), name="   ", merge=False)


def test_delete_removes_the_tag(teacher_ctx: Ctx) -> None:
    tag_id = new_tag(teacher_ctx, "Cell")

    assert delete_tag(teacher_ctx, tag_id=tag_id) == 0
    assert names() == []


def test_unknown_tag_is_not_found(teacher_ctx: Ctx) -> None:
    with pytest.raises(NotFound):
        rename_tag(teacher_ctx, tag_id=uuid4(), name="x", merge=False)
    with pytest.raises(NotFound):
        delete_tag(teacher_ctx, tag_id=uuid4())


def test_list_shows_every_tag_with_counts(teacher_ctx: Ctx) -> None:
    new_tag(teacher_ctx, "Cell")
    new_tag(teacher_ctx, "Mitosis", kind=TagKind.TOPIC)

    usages = list_tags_with_usage(teacher_ctx, kind=None, search=None)
    chapters = list_tags_with_usage(teacher_ctx, kind=CHAPTER, search="CE")

    assert [(u.tag.name, u.question_count, u.test_count) for u in usages] == [
        ("Cell", 0, 0),
        ("Mitosis", 0, 0),
    ]
    assert [u.tag.name for u in chapters] == ["Cell"]


def test_suggestions_put_prefix_matches_first(teacher_ctx: Ctx) -> None:
    for name in ("Intercellular", "Cell", "Cerebral system", "Nucleus"):
        new_tag(teacher_ctx, name)

    suggested = suggest_tags(teacher_ctx, kind=CHAPTER, typed="ce")

    assert [tag.name for tag in suggested] == ["Cell", "Cerebral system", "Intercellular"]


def test_only_the_teacher_manages_tags(make_ctx: MakeCtx) -> None:
    student = Actor(user_id=uuid4(), role=Role.STUDENT, student_status=StudentStatus.ACTIVE)

    with pytest.raises(Forbidden):
        list_tags_with_usage(make_ctx(student), kind=None, search=None)


def test_counts_merge_and_delete_follow_the_questions(teacher_ctx: Ctx) -> None:
    typo, real = new_tag(teacher_ctx, "Genetcs"), new_tag(teacher_ctx, "Genetics")
    first, second = make_test(), make_test(title="Revision")
    make_question(make_section(first), tag_ids=[typo, real])
    make_question(make_section(second), tag_ids=[typo])
    make_question(make_section(second, 1), tag_ids=[real])

    before = {
        u.tag.name: (u.question_count, u.test_count)
        for u in list_tags_with_usage(teacher_ctx, kind=CHAPTER, search=None)
    }
    rename_tag(teacher_ctx, tag_id=typo, name="Genetics", merge=True)
    after = list_tags_with_usage(teacher_ctx, kind=CHAPTER, search=None)

    assert before == {"Genetcs": (2, 2), "Genetics": (2, 2)}
    # The question that had both keeps one; the other two move over
    assert [(u.tag.name, u.question_count, u.test_count) for u in after] == [("Genetics", 3, 2)]
    assert delete_tag(teacher_ctx, tag_id=real) == 3
