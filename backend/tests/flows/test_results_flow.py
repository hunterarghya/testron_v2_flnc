"""Results end to end (domain_model.md §6.3-6.4; testing_strategy.md §3.7 "Locked test",
"Auto-publish delayed"; E-27, E-28; H-2, H-4)."""

from datetime import timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pytest_django import DjangoAssertNumQueries

from core.clock import FrozenClock
from core.context import Ctx
from core.errors import Forbidden
from modules.assignments.domain.publishing import PublicationChanges
from modules.assignments.domain.values import PublicationMode, PublishContent
from modules.assignments.services.commands.publish_results import publish_results
from modules.assignments.services.commands.unpublish_results import unpublish_results
from modules.assignments.services.commands.update_publication import update_publication
from modules.delivery.services.commands.override_disqualification import override_disqualification
from modules.delivery.services.commands.submit_attempt import submit_attempt
from modules.results.domain.errors import ResultsNotPublished
from modules.results.services.queries.export_gradebook_csv import export_gradebook_csv
from modules.results.services.queries.get_answer_sheet import get_answer_sheet
from modules.results.services.queries.get_badges import get_badges
from modules.results.services.queries.get_dashboard import get_dashboard
from modules.results.services.queries.get_gradebook import get_gradebook
from modules.results.services.queries.get_my_result import get_my_result
from modules.results.services.queries.get_question_stats import get_question_stats
from modules.results.services.queries.list_my_past_tests import list_my_past_tests
from modules.results.services.queries.list_results_inbox import InboxTab, list_results_inbox
from tests.factories.assignments import assign, exam_test, locked, start, teacher_ctx
from tests.factories.delivery import answer, as_student, begin, choice, numeric, option_id, stored
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
HOUR = timedelta(hours=1)


def _sat(clock: FrozenClock) -> tuple[UUID, dict[str, UUID], dict[str, UUID]]:
    """A closed locked test: Mou scores 12, Arjun 2, Rahul never came. Returns the
    assignment, the students and their attempts by name."""
    names = {
        "Mou": make_student(name="Mou").id,
        "Arjun": make_student(name="Arjun").id,
        "Rahul": make_student(name="Rahul").id,
    }
    assignment_id = assign(list(names.values()), now=clock.now(), test=exam_test(), window=locked())
    start(assignment_id, now=clock.now())
    attempts = {}
    for name, picks in (("Mou", ("A", "A", "46")), ("Arjun", ("A", "B", "45"))):
        ctx = as_student(names[name], now=clock.now())
        state = begin(ctx, assignment_id)
        answer(ctx, state, 1, choice(option_id(state, 1, picks[0])))
        answer(ctx, state, 2, choice(option_id(state, 2, picks[1])))
        answer(ctx, state, 3, numeric(picks[2]))
        submit_attempt(ctx, attempt_id=state.attempt.id, client_id=state.attempt.active_client_id)
        attempts[name] = state.attempt.id
    clock.advance(hours=2)
    return assignment_id, names, attempts


def _student(clock: FrozenClock, student_id: UUID) -> Ctx:
    return as_student(student_id, now=clock.now())


def test_the_gradebook_ranks_everyone_and_lists_the_absent_h4(
    frozen_clock: FrozenClock, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    assignment_id, _, _ = _sat(frozen_clock)
    teacher = teacher_ctx(frozen_clock.now())

    with django_assert_max_num_queries(20):
        book = get_gradebook(teacher, assignment_id=assignment_id)

    rows = [(r.name, r.status, r.placing.rank if r.placing else None) for r in book.rows]
    assert rows == [("Mou", "SUBMITTED", 1), ("Arjun", "SUBMITTED", 2), ("Rahul", "ABSENT", None)]
    assert book.stats is not None
    assert (book.stats.mean, book.attempted, book.absent) == (Decimal("7.00"), 2, 1)
    stats = get_question_stats(teacher, assignment_id=assignment_id)
    assert [(s.number, s.stat.correct, s.stat.top_wrong_count) for s in stats] == [
        (1, 2, 0),
        (2, 1, 1),
        (3, 1, 0),
    ]
    csv = export_gradebook_csv(teacher, assignment_id=assignment_id)
    assert csv.text.startswith("﻿Student,Take,Status,Score,Max,Rank,")
    assert csv.name.endswith(" - Gradebook.csv")


def test_results_show_only_once_published_and_only_what_was_chosen(
    frozen_clock: FrozenClock,
) -> None:
    assignment_id, names, attempts = _sat(frozen_clock)
    mou = _student(frozen_clock, names["Mou"])
    teacher = teacher_ctx(frozen_clock.now())

    assert [c.state for c in list_my_past_tests(mou)] == ["AWAITING_RESULTS"]
    with pytest.raises(ResultsNotPublished):
        get_my_result(mou, attempt_id=attempts["Mou"])
    assert get_badges(teacher).results_to_publish == 1

    publish_results(teacher, assignment_id=assignment_id, changes=PublicationChanges())
    plain = get_my_result(mou, attempt_id=attempts["Mou"]).result
    assert (plain.attempt.score, plain.questions, plain.placing) == (Decimal("12.00"), None, None)

    publish_results(
        teacher,
        assignment_id=assignment_id,
        changes=PublicationChanges(content=PublishContent.ANSWER_REVIEW, show_rank_and_stats=True),
    )
    full = get_my_result(mou, attempt_id=attempts["Mou"]).result
    assert full.placing is not None
    assert (full.placing.rank, full.placing.pool) == (1, 2)
    assert full.questions is not None
    assert full.questions[2].correct == {
        "type": "NUMERICAL",
        "answer": "46.000000",
        "tolerance": "0.000000",
    }
    card = list_my_past_tests(mou)[0]
    assert (card.state, card.score, card.placing and card.placing.rank) == (
        "PUBLISHED",
        Decimal("12.00"),
        1,
    )
    assert list_results_inbox(teacher, tab=InboxTab.PUBLISHED)[0].average_pct == Decimal(58)

    unpublish_results(teacher, assignment_id=assignment_id)
    assert [c.state for c in list_my_past_tests(mou)] == ["AWAITING_RESULTS"]


def test_a_missed_test_shows_as_missed(frozen_clock: FrozenClock) -> None:
    _, names, _ = _sat(frozen_clock)
    cards = list_my_past_tests(_student(frozen_clock, names["Rahul"]))
    assert [c.state for c in cards] == ["MISSED"]


def test_auto_publish_delayed_needs_no_action_e27(frozen_clock: FrozenClock) -> None:
    assignment_id, names, attempts = _sat(frozen_clock)
    teacher = teacher_ctx(frozen_clock.now())
    update_publication(
        teacher,
        assignment_id=assignment_id,
        changes=PublicationChanges(mode=PublicationMode.AUTO_DELAYED, delay_s=7200),
    )
    with pytest.raises(ResultsNotPublished):
        get_my_result(_student(frozen_clock, names["Arjun"]), attempt_id=attempts["Arjun"])

    frozen_clock.advance(hours=1)
    seen = get_my_result(_student(frozen_clock, names["Arjun"]), attempt_id=attempts["Arjun"])
    assert seen.result.attempt.score == Decimal("2.00")


def test_the_dashboard_counts_what_needs_the_teacher(frozen_clock: FrozenClock) -> None:
    assignment_id, _, _ = _sat(frozen_clock)
    board = get_dashboard(teacher_ctx(frozen_clock.now()))
    assert board.results_to_publish == 1
    assert [r.row.record.id for r in board.recent] == [assignment_id]
    assert board.live == []


def test_a_disqualified_student_sees_no_score_until_overridden_dm5(
    frozen_clock: FrozenClock,
) -> None:
    assignment_id, names, attempts = _sat(frozen_clock)
    row = stored(attempts["Arjun"])
    row.end_reason = "DISQUALIFIED"
    row.save()
    teacher = teacher_ctx(frozen_clock.now())
    publish_results(
        teacher, assignment_id=assignment_id, changes=PublicationChanges(show_rank_and_stats=True)
    )
    arjun = _student(frozen_clock, names["Arjun"])

    assert [c.state for c in list_my_past_tests(arjun)] == ["DISQUALIFIED"]
    hidden = get_my_result(arjun, attempt_id=attempts["Arjun"])
    assert (hidden.score_hidden, hidden.result.placing) == (True, None)
    book = get_gradebook(teacher, assignment_id=assignment_id)
    assert [(r.name, r.placing) for r in book.rows if r.name == "Arjun"] == [("Arjun", None)]

    flags = get_answer_sheet(teacher, attempt_id=attempts["Arjun"]).flags
    assert (flags.max_warnings, flags.action, flags.override_reason) == (3, "AUTO_SUBMIT", None)
    override_disqualification(teacher, attempt_id=attempts["Arjun"], reason="Power cut")
    override_disqualification(teacher, attempt_id=attempts["Arjun"], reason="Again")
    flags = get_answer_sheet(teacher, attempt_id=attempts["Arjun"]).flags
    assert (flags.overridden_at, flags.override_reason) == (frozen_clock.now(), "Power cut")
    shown = get_my_result(arjun, attempt_id=attempts["Arjun"])
    assert shown.score_hidden is False
    assert shown.result.placing is not None
    assert shown.result.placing.rank == 2


def test_past_tests_and_results_are_for_students_only(frozen_clock: FrozenClock) -> None:
    _, _, attempts = _sat(frozen_clock)
    teacher = teacher_ctx(frozen_clock.now())
    with pytest.raises(Forbidden):
        list_my_past_tests(teacher)
    with pytest.raises(Forbidden):
        get_my_result(teacher, attempt_id=attempts["Mou"])
