"""add_question, update_question, delete_question, duplicate_question (T-03 autosave)."""

from decimal import Decimal
from uuid import UUID

import pytest

from conftest import MakeCtx
from core.context import Ctx
from core.errors import FieldsInvalid
from core.rich_content import EMPTY_DOC
from modules.authoring.domain.question_patch import OptionInput, QuestionChanges
from modules.authoring.domain.values import QuestionType
from modules.authoring.services.commands.delete_question import delete_question
from modules.authoring.services.commands.duplicate_question import duplicate_question
from modules.authoring.services.commands.update_question import update_question
from modules.authoring.services.queries.list_tags_with_usage import list_tags_with_usage
from modules.authoring.tests.services.editor_helpers import (
    TEACHER,
    add,
    latest,
    new_test,
    question_order,
    words,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(TEACHER)


@pytest.fixture
def test_id(ctx: Ctx) -> UUID:
    return new_test(ctx).id


def save(ctx: Ctx, test_id: UUID, question_id: UUID, changes: QuestionChanges) -> None:
    update_question(
        ctx, question_id=question_id, revision=latest(ctx, test_id).revision, changes=changes
    )


def complete(question_type: QuestionType = QuestionType.MCQ) -> QuestionChanges:
    return QuestionChanges(
        type=question_type,
        stem=words("Which organelle makes energy?"),
        options=[
            OptionInput(None, words("Mitochondria"), True),
            OptionInput(None, words("Golgi"), False),
        ],
    )


def test_a_new_choice_question_has_four_empty_options(ctx: Ctx, test_id: UUID) -> None:
    question_id = add(ctx, test_id)
    question = latest(ctx, test_id).question(question_id)

    assert (question.type, len(question.options), question.stem) == (QuestionType.MCQ, 4, EMPTY_DOC)
    assert {p.code for p in latest(ctx, test_id).problems()} == {
        "stem_empty",
        "option_empty",
        "no_correct_option",
    }


def test_questions_go_where_asked(ctx: Ctx, test_id: UUID) -> None:
    first = add(ctx, test_id)
    third = add(ctx, test_id)
    second = add(ctx, test_id, after=first)

    assert question_order(ctx, test_id) == [[first, second, third]]


def test_a_complete_save_clears_the_problems(ctx: Ctx, test_id: UUID) -> None:
    question_id = add(ctx, test_id)

    save(ctx, test_id, question_id, complete())

    document = latest(ctx, test_id)
    assert document.problems() == []
    assert document.question(question_id).options[0].content == words("Mitochondria")
    assert document.totals().marks == Decimal(4)


def test_kept_options_keep_their_ids(ctx: Ctx, test_id: UUID) -> None:
    question_id = add(ctx, test_id)
    save(ctx, test_id, question_id, complete())
    first, second = latest(ctx, test_id).question(question_id).options

    save(
        ctx,
        test_id,
        question_id,
        {
            "options": [
                OptionInput(second.id, words("Golgi body"), True),
                OptionInput(None, words("Ribosome"), False),
            ]
        },
    )

    options = latest(ctx, test_id).question(question_id).options
    assert options[0].id == second.id
    assert first.id not in [o.id for o in options]
    assert [o.content for o in options] == [words("Golgi body"), words("Ribosome")]


def test_an_option_of_another_question_is_refused(ctx: Ctx, test_id: UUID) -> None:
    mine, other = add(ctx, test_id), add(ctx, test_id)
    foreign = latest(ctx, test_id).question(other).options[0].id

    with pytest.raises(FieldsInvalid):
        save(ctx, test_id, mine, {"options": [OptionInput(foreign, words("x"), True)]})


def test_switching_to_numerical_drops_options_and_back_clears_the_answer(
    ctx: Ctx, test_id: UUID
) -> None:
    question_id = add(ctx, test_id)

    save(
        ctx,
        test_id,
        question_id,
        {
            "type": QuestionType.NUMERICAL,
            "numeric_answer": Decimal("6.02"),
            "numeric_tolerance": Decimal("0.01"),
        },
    )
    numerical = latest(ctx, test_id).question(question_id)
    save(ctx, test_id, question_id, {"type": QuestionType.MSQ})
    choice = latest(ctx, test_id).question(question_id)

    assert (numerical.options, numerical.numeric_answer) == ((), Decimal("6.020000"))
    assert (choice.numeric_answer, choice.numeric_tolerance, choice.options) == (
        None,
        Decimal(0),
        (),
    )


def test_mcq_to_msq_and_back_keeps_two_correct_options_as_a_problem(
    ctx: Ctx, test_id: UUID
) -> None:
    question_id = add(ctx, test_id)
    both = [OptionInput(None, words("A"), True), OptionInput(None, words("B"), True)]
    save(ctx, test_id, question_id, {**complete(QuestionType.MSQ), "options": both})

    save(ctx, test_id, question_id, {"type": QuestionType.MCQ})

    assert [p.code for p in latest(ctx, test_id).problems()] == ["mcq_multiple_correct"]


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"stem": {"v": 1, "type": "doc", "content": [{"type": "heading"}]}}, "stem"),
        (
            {
                "options": [
                    OptionInput(None, {"v": 1, "type": "doc", "content": [{"type": "table"}]}, True)
                ]
            },
            "options.0.content",
        ),
        ({"marks_override": Decimal(0)}, "marks_override"),
        ({"time_override_s": 2}, "time_override_s"),
        ({"numeric_answer": Decimal(5)}, "numeric_answer"),
    ],
)
def test_bad_values_are_field_errors(
    ctx: Ctx, test_id: UUID, changes: QuestionChanges, field: str
) -> None:
    question_id = add(ctx, test_id)

    with pytest.raises(FieldsInvalid) as error:
        save(ctx, test_id, question_id, changes)

    assert error.value.field_errors()[0].field == field


def test_tags_come_by_name_and_are_replaced_per_kind(ctx: Ctx, test_id: UUID) -> None:
    question_id = add(ctx, test_id)
    save(
        ctx, test_id, question_id, {"chapter_tags": ["Cell", "genetics"], "topic_tags": ["Mitosis"]}
    )

    save(ctx, test_id, question_id, {"chapter_tags": ["cell"]})

    question = latest(ctx, test_id).question(question_id)
    assert ([t.name for t in question.chapter_tags], [t.name for t in question.topic_tags]) == (
        ["Cell"],
        ["Mitosis"],
    )
    assert {
        u.tag.name: u.question_count for u in list_tags_with_usage(ctx, kind=None, search=None)
    } == {"Cell": 1, "genetics": 0, "Mitosis": 1}


def test_duplicate_lands_right_after_with_options_and_tags(ctx: Ctx, test_id: UUID) -> None:
    first, last = add(ctx, test_id), add(ctx, test_id)
    save(ctx, test_id, first, {**complete(), "chapter_tags": ["Cell"]})

    copy_id = duplicate_question(
        ctx, question_id=first, revision=latest(ctx, test_id).revision
    ).made

    copy = latest(ctx, test_id).question(copy_id)
    assert question_order(ctx, test_id) == [[first, copy_id, last]]
    assert ([o.content for o in copy.options], [t.name for t in copy.chapter_tags]) == (
        [words("Mitochondria"), words("Golgi")],
        ["Cell"],
    )


def test_delete_closes_the_gap(ctx: Ctx, test_id: UUID) -> None:
    first, middle, last = add(ctx, test_id), add(ctx, test_id), add(ctx, test_id)

    delete_question(ctx, question_id=middle, revision=latest(ctx, test_id).revision)

    document = latest(ctx, test_id)
    assert [(q.id, q.position) for q in document.sections[0].questions] == [(first, 0), (last, 1)]
