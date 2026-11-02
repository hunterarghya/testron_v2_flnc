"""create_test, get_test_document, update_test, sections and restructure (T-02, T-03, T-04)."""

from decimal import Decimal
from uuid import UUID

import pytest
from pytest_django import DjangoAssertNumQueries

from conftest import MakeCtx
from core.context import Ctx
from core.errors import FieldsInvalid, Forbidden
from modules.authoring.domain.drafts import Marking
from modules.authoring.domain.errors import SectionNotEmpty, TestChangedElsewhere
from modules.authoring.domain.settings_patch import SettingsPatch, TimingPatch
from modules.authoring.domain.values import TimingKind
from modules.authoring.services.commands.add_section import add_section
from modules.authoring.services.commands.delete_section import WithQuestions, delete_section
from modules.authoring.services.commands.restructure_test import restructure_test
from modules.authoring.services.commands.update_app_settings import update_app_settings
from modules.authoring.services.commands.update_question import update_question
from modules.authoring.services.commands.update_section import update_section
from modules.authoring.services.commands.update_test import update_test
from modules.authoring.tests.services.editor_helpers import (
    TEACHER,
    add,
    latest,
    new_test,
    question_order,
    words,
)

pytestmark = pytest.mark.django_db
SECTIONED = SettingsPatch(timing=TimingPatch(TimingKind.SECTIONED))


@pytest.fixture
def ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(TEACHER)


def sectioned_with_two(ctx: Ctx) -> tuple[UUID, list[list[UUID]]]:
    """A sectioned test: section 1 with two questions, section 2 with one."""
    test = new_test(ctx)
    q1, q2 = add(ctx, test.id), add(ctx, test.id)
    update_test(
        ctx,
        test_id=test.id,
        revision=latest(ctx, test.id).revision,
        changes={"settings": SECTIONED},
    )
    document = latest(ctx, test.id)
    second = add_section(
        ctx,
        test_id=test.id,
        revision=document.revision,
        after_section_id=document.sections[0].id,
        title="Botany",
        duration_s=600,
    ).made
    q3 = add(ctx, test.id)
    restructure_test(
        ctx,
        test_id=test.id,
        revision=latest(ctx, test.id).revision,
        wanted=[(document.sections[0].id, [q1, q2]), (second, [q3])],
    )
    return test.id, [[q1, q2], [q3]]


def test_a_new_test_takes_the_teachers_defaults(ctx: Ctx) -> None:
    update_app_settings(ctx, changes={"default_marks": Decimal(2)})

    test = new_test(ctx)

    assert (test.title, test.revision, len(test.sections)) == ("Untitled test", 1, 1)
    assert test.settings.marking.marks == Decimal(2)
    assert test.settings.timing.kind is TimingKind.TOTAL
    assert [p.code for p in test.problems()] == ["test_empty"]


def test_reading_a_test_takes_six_queries(
    ctx: Ctx, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    test = new_test(ctx)
    for _ in range(5):
        question_id = add(ctx, test.id)
        update_question(
            ctx,
            question_id=question_id,
            revision=latest(ctx, test.id).revision,
            changes={"chapter_tags": ["Cell"], "topic_tags": ["Mitosis"]},
        )

    # The test, sections, questions, options, question tags and tag names
    with django_assert_num_queries(6):
        latest(ctx, test.id)


def test_a_stale_revision_is_refused(ctx: Ctx) -> None:
    test = new_test(ctx)
    update_test(ctx, test_id=test.id, revision=1, changes={"title": "Cell Biology"})

    with pytest.raises(TestChangedElsewhere) as error:
        update_test(ctx, test_id=test.id, revision=1, changes={"title": "Genetics"})

    assert error.value.context == {"revision": 2}
    assert latest(ctx, test.id).title == "Cell Biology"


def test_title_instructions_and_settings_change(ctx: Ctx) -> None:
    test = new_test(ctx)
    result = update_test(
        ctx,
        test_id=test.id,
        revision=1,
        changes={
            "title": "  Cell   Biology ",
            "instructions": words("Read carefully"),
            "settings": SettingsPatch(
                shuffle_options=True, marking=Marking(Decimal(3), Decimal(0))
            ),
        },
    )

    after = result.document
    assert (result.revision, after.title, after.settings.shuffle_options) == (
        2,
        "Cell Biology",
        True,
    )
    assert after.settings.marking == Marking(Decimal("3.00"), Decimal("0.00"))
    assert after.instructions == words("Read carefully")


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"title": "   "}, "title"),
        (
            {"instructions": {"v": 1, "type": "doc", "content": [{"type": "heading"}]}},
            "instructions",
        ),
        (
            {"settings": SettingsPatch(timing=TimingPatch(TimingKind.TOTAL, duration_s=30))},
            "settings.timing.duration_s",
        ),
    ],
)
def test_bad_values_are_field_errors(ctx: Ctx, changes: dict[str, object], field: str) -> None:
    test = new_test(ctx)

    with pytest.raises(FieldsInvalid) as error:
        update_test(ctx, test_id=test.id, revision=1, changes=changes)  # type: ignore[arg-type]

    assert error.value.field_errors()[0].field == field


def test_going_sectioned_keeps_the_total_as_the_sections_duration(ctx: Ctx) -> None:
    test = new_test(ctx)

    after = update_test(ctx, test_id=test.id, revision=1, changes={"settings": SECTIONED}).document

    assert after.settings.timing.kind is TimingKind.SECTIONED
    assert after.sections[0].duration_s == 3600


def test_leaving_sectioned_merges_the_sections_in_order(ctx: Ctx) -> None:
    test_id, order = sectioned_with_two(ctx)
    to_total = SettingsPatch(timing=TimingPatch(TimingKind.TOTAL))

    after = update_test(
        ctx, test_id=test_id, revision=latest(ctx, test_id).revision, changes={"settings": to_total}
    ).document

    assert question_order(ctx, test_id) == [[*order[0], *order[1]]]
    # Sections of 3600 s and 600 s add up
    assert after.settings.timing.duration_s == 4200


def test_sections_need_sectioned_timing(ctx: Ctx) -> None:
    test = new_test(ctx)

    with pytest.raises(FieldsInvalid):
        add_section(
            ctx, test_id=test.id, revision=1, after_section_id=None, title="", duration_s=None
        )


def test_a_section_can_be_renamed_and_timed(ctx: Ctx) -> None:
    test_id, _ = sectioned_with_two(ctx)
    section = latest(ctx, test_id).sections[1]

    update_section(
        ctx,
        section_id=section.id,
        revision=latest(ctx, test_id).revision,
        changes={"title": " Zoology ", "duration_s": None},
    )

    renamed = latest(ctx, test_id).sections[1]
    assert (renamed.title, renamed.duration_s) == ("Zoology", None)
    assert "section_no_duration" in [p.code for p in latest(ctx, test_id).problems()]


def test_deleting_a_section_asks_what_to_do_with_its_questions(ctx: Ctx) -> None:
    test_id, order = sectioned_with_two(ctx)
    second = latest(ctx, test_id).sections[1].id

    with pytest.raises(SectionNotEmpty):
        delete_section(
            ctx, section_id=second, revision=latest(ctx, test_id).revision, questions_choice=None
        )
    delete_section(
        ctx,
        section_id=second,
        revision=latest(ctx, test_id).revision,
        questions_choice=WithQuestions.MOVE_TO_PREVIOUS,
    )

    assert question_order(ctx, test_id) == [[*order[0], *order[1]]]


def test_deleting_the_first_section_can_drop_its_questions(ctx: Ctx) -> None:
    test_id, order = sectioned_with_two(ctx)
    first = latest(ctx, test_id).sections[0].id

    delete_section(
        ctx,
        section_id=first,
        revision=latest(ctx, test_id).revision,
        questions_choice=WithQuestions.DELETE,
    )

    assert question_order(ctx, test_id) == [order[1]]
    with pytest.raises(FieldsInvalid):
        delete_section(
            ctx,
            section_id=latest(ctx, test_id).sections[0].id,
            revision=latest(ctx, test_id).revision,
            questions_choice=WithQuestions.DELETE,
        )


def test_restructure_moves_questions_between_sections(ctx: Ctx) -> None:
    test_id, order = sectioned_with_two(ctx)
    first, second = (s.id for s in latest(ctx, test_id).sections)

    restructure_test(
        ctx,
        test_id=test_id,
        revision=latest(ctx, test_id).revision,
        wanted=[(second, [order[0][1], *order[1]]), (first, [order[0][0]])],
    )

    assert question_order(ctx, test_id) == [[order[0][1], *order[1]], [order[0][0]]]
    with pytest.raises(FieldsInvalid):
        restructure_test(
            ctx, test_id=test_id, revision=latest(ctx, test_id).revision, wanted=[(first, order[0])]
        )


def test_only_the_teacher_edits(make_ctx: MakeCtx, ctx: Ctx) -> None:
    test = new_test(ctx)

    with pytest.raises(Forbidden):
        update_test(make_ctx(), test_id=test.id, revision=1, changes={"title": "Mine"})
