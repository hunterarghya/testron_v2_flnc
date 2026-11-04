"""Tag performance end to end (domain_model.md §6.5; build_phases.md Phase 7 required tests:
renamed and deleted tags, only visible attempts for students; security.md A-11)."""

from decimal import Decimal
from uuid import UUID

import pytest
from pytest_django import DjangoAssertNumQueries

from core.clock import FrozenClock
from modules.assignments.domain.publishing import PublicationChanges
from modules.assignments.services.commands.publish_results import publish_results
from modules.authoring.services.commands.delete_tag import delete_tag
from modules.authoring.services.commands.rename_tag import rename_tag
from modules.delivery.services.commands.submit_attempt import submit_attempt
from modules.results.domain.errors import PerformanceNotShared
from modules.results.services.performance_view import PerformanceView
from modules.results.services.queries.get_group_performance import get_group_performance
from modules.results.services.queries.get_my_performance import get_my_performance
from modules.results.services.queries.get_student_performance import get_student_performance
from modules.students.services.commands.share_performance import share_performance
from modules.tagging.public import TagKind, ensure_tags_by_name
from tests.clients import logged_in, send
from tests.factories.assignments import assign, locked, start, teacher_ctx, the_teacher
from tests.factories.authoring import make_question, make_section, make_test
from tests.factories.delivery import answer, as_student, begin, choice, option_id
from tests.factories.students import make_group, make_student

pytestmark = pytest.mark.django_db


def _sat(clock: FrozenClock) -> tuple[UUID, dict[str, UUID], dict[str, UUID]]:
    """Q1 is tagged Cell (chapter) and Mitochondria (topic), Q2 Genetics (chapter); +4/-1.
    Mou gets Q1 right and Q2 wrong; Arjun gets Q1 wrong and skips Q2."""
    teacher = teacher_ctx(clock.now())
    cell, genetics = ensure_tags_by_name(teacher, kind=TagKind.CHAPTER, names=["Cell", "Genetics"])
    (mito,) = ensure_tags_by_name(teacher, kind=TagKind.TOPIC, names=["Mitochondria"])
    test = make_test(shuffle_questions=False, shuffle_options=False)
    section = make_section(test)
    make_question(section, 0, tag_ids=[cell.id, mito.id])
    make_question(section, 1, tag_ids=[genetics.id])
    names = {"Mou": make_student(name="Mou").id, "Arjun": make_student(name="Arjun").id}
    assignment_id = assign(list(names.values()), now=clock.now(), test=test, window=locked())
    start(assignment_id, now=clock.now())
    for name, picks in (("Mou", ("A", "B")), ("Arjun", ("B", None))):
        ctx = as_student(names[name], now=clock.now())
        state = begin(ctx, assignment_id)
        for number, pick in enumerate(picks, start=1):
            if pick:
                answer(ctx, state, number, choice(option_id(state, number, pick)))
        submit_attempt(ctx, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id)
    clock.advance(hours=2)
    tags = {"Cell": cell.id, "Genetics": genetics.id, "Mitochondria": mito.id}
    return assignment_id, names, tags


def _rows(view: PerformanceView) -> list[tuple[str, str, str, str]]:
    return [
        (
            r.tag.name,
            str(r.performance.score_pct),
            str(r.performance.accuracy_pct),
            str(r.performance.attempted_pct),
        )
        for r in view.chapters + view.topics
    ]


def test_a_student_sees_only_a_shared_report_built_from_visible_results_a11(
    frozen_clock: FrozenClock,
) -> None:
    assignment_id, names, _ = _sat(frozen_clock)
    teacher = teacher_ctx(frozen_clock.now())
    mou = as_student(names["Mou"], now=frozen_clock.now())

    with pytest.raises(PerformanceNotShared):
        get_my_performance(mou)
    share_performance(teacher, student_ids=[names["Mou"]], group_id=None)
    assert get_my_performance(mou).based_on_attempts == 0
    # The teacher sees the unpublished attempt already
    assert get_student_performance(teacher, student_id=names["Mou"]).based_on_attempts == 1

    publish_results(teacher, assignment_id=assignment_id, changes=PublicationChanges())
    view = get_my_performance(mou)

    assert _rows(view) == [
        ("Genetics", "-25.0", "0.0", "100.0"),
        ("Cell", "100.0", "100.0", "100.0"),
        ("Mitochondria", "100.0", "100.0", "100.0"),
    ]
    assert [p.score_pct for p in view.trend] == [Decimal("37.5")]


def test_a_renamed_tag_keeps_its_history_and_a_deleted_one_drops_out(
    frozen_clock: FrozenClock,
) -> None:
    _, names, tags = _sat(frozen_clock)
    teacher = teacher_ctx(frozen_clock.now())

    rename_tag(teacher, tag_id=tags["Cell"], name="Cell Biology", merge=False)
    delete_tag(teacher, tag_id=tags["Genetics"])
    view = get_student_performance(teacher, student_id=names["Mou"])

    assert [r.tag.name for r in view.chapters] == ["Cell Biology"]
    assert view.chapters[0].performance.score_pct == Decimal("100.0")


def test_a_group_report_adds_up_everyone_and_trends_by_test(
    frozen_clock: FrozenClock, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    assignment_id, names, _ = _sat(frozen_clock)
    group = make_group("Batch A", list(names.values()))
    teacher = teacher_ctx(frozen_clock.now())

    with django_assert_max_num_queries(8):
        found = get_group_performance(teacher, group_id=group.id)

    assert (found.group_name, found.students, found.report.based_on_attempts) == ("Batch A", 2, 2)
    # Genetics: -1 + 0 of 8; Cell: +4 - 1 of 8; Arjun answered 1 of the 2 Genetics questions
    assert _rows(found.report)[:2] == [
        ("Genetics", "-12.5", "0.0", "50.0"),
        ("Cell", "37.5", "50.0", "100.0"),
    ]
    assert [(p.key, p.score_pct) for p in found.report.trend] == [(assignment_id, Decimal("12.5"))]


def test_performance_over_http(frozen_clock: FrozenClock) -> None:
    _, names, _ = _sat(frozen_clock)
    group = make_group("Batch A", list(names.values()))
    teacher = logged_in(the_teacher().email)
    student = make_student(name="Rina")

    hidden = send(logged_in(student.email), "get", "/api/v1/my/performance")
    mine = send(teacher, "get", f"/api/v1/admin/students/{names['Mou']}/performance").json()
    theirs = send(teacher, "get", f"/api/v1/admin/groups/{group.id}/performance").json()

    assert (hidden.status_code, hidden.json()["code"]) == (404, "performance_not_shared")
    assert mine["chapters"][0]["tag"]["name"] == "Genetics"
    assert set(mine["trend"][0]) == {"attempt_id", "label", "ended_at", "score_pct"}
    assert (theirs["group_name"], theirs["trend"][0]["score_pct"]) == ("Batch A", "12.5")
