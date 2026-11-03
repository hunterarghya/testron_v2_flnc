"""The plan (domain_model.md §5.4: seeded, stored, shuffled within sections) and the answer
shape rules (§3.6 #4, E-18)."""

from uuid import UUID, uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from modules.delivery.domain.answers import (
    ChoiceAnswer,
    NumericAnswer,
    answer_json,
    ensure_answer_fits,
    read_answer,
)
from modules.delivery.domain.errors import AnswerInvalid
from modules.delivery.domain.paper import PaperQuestion, PaperView, read_paper
from modules.delivery.domain.plan import build_plan, plan_json, read_plan
from modules.delivery.domain.values import StageKind

DOC = {"v": 1, "type": "doc", "content": []}


def _question(kind: str = "MCQ", options: int = 4, time_s: int | None = None) -> dict[str, object]:
    question: dict[str, object] = {
        "id": str(uuid4()),
        "type": kind,
        "stem": DOC,
        "marks": "4.00",
        "negative_marks": "1.00",
        "time_s": time_s,
        "tag_ids": [],
    }
    if kind != "NUMERICAL":
        question["options"] = [{"id": str(uuid4()), "content": DOC} for _ in range(options)]
    return question


def paper(
    kind: str = "TOTAL", *, shuffle: bool = True, sizes: tuple[int, ...] = (3, 2)
) -> PaperView:
    sections = [
        {
            "id": str(uuid4()),
            "title": f"Section {n}",
            "instructions": None,
            "duration_s": 600 if kind == "SECTIONED" else None,
            "questions": [_question(time_s=45) for _ in range(size)],
        }
        for n, size in enumerate(sizes)
    ]
    return read_paper(
        {
            "v": 1,
            "title": "Cell Biology",
            "instructions": None,
            "timing": {"kind": kind, "allow_return": True, "total_duration_s": 1200},
            "shuffle": {"questions": shuffle, "options": shuffle},
            "sections": sections,
        }
    )


def test_a_total_timer_test_is_one_stage_with_every_question() -> None:
    view = paper()
    plan = build_plan(view, seed=7)
    assert [(s.kind, s.duration_s) for s in plan.stages] == [(StageKind.WHOLE, 1200)]
    assert sorted(plan.question_ids()) == sorted(view.questions())


def test_shuffling_keeps_questions_inside_their_section() -> None:
    view = paper(sizes=(5, 5))
    order = build_plan(view, seed=3).question_ids()
    first = {q.id for q in view.sections[0].questions}
    assert set(order[:5]) == first


def test_sectioned_and_rapid_fire_stages() -> None:
    sectioned = build_plan(paper("SECTIONED"), seed=1)
    assert [(s.kind, s.duration_s, len(s.question_ids)) for s in sectioned.stages] == [
        (StageKind.SECTION, 600, 3),
        (StageKind.SECTION, 600, 2),
    ]
    rapid = build_plan(paper("PER_QUESTION"), seed=1)
    assert [(s.kind, s.duration_s) for s in rapid.stages] == [(StageKind.QUESTION, 45)] * 5
    assert rapid.stage_of(rapid.stages[3].question_ids[0]) == 3
    assert rapid.stage_of(uuid4()) is None


def test_without_shuffling_the_teachers_order_is_kept() -> None:
    view = paper(shuffle=False)
    plan = build_plan(view, seed=99)
    assert plan.question_ids() == list(view.questions())
    first = next(iter(view.questions().values()))
    assert plan.option_order[first.id] == first.option_ids


def test_v1_f38_shuffle_is_server_side_and_deterministic() -> None:
    view = paper(sizes=(8,))
    assert build_plan(view, seed=42) == build_plan(view, seed=42)
    orders = {tuple(build_plan(view, seed=s).question_ids()) for s in range(20)}
    assert len(orders) > 1


@given(st.integers(0, 2**63 - 1))
def test_a_stored_plan_reads_back_the_same(seed: int) -> None:
    plan = build_plan(paper("SECTIONED"), seed=seed)
    assert read_plan(plan_json(plan)) == plan


@given(st.integers(0, 2**63 - 1))
def test_the_plan_is_a_permutation_within_each_stage(seed: int) -> None:
    view = paper("SECTIONED", sizes=(4, 3))
    for stage, section in zip(build_plan(view, seed).stages, view.sections, strict=True):
        assert sorted(stage.question_ids) == sorted(q.id for q in section.questions)


MCQ = paper(shuffle=False).sections[0].questions[0]
NUMERICAL = (
    read_paper(
        {
            "title": "N",
            "timing": {"kind": "TOTAL", "allow_return": False, "total_duration_s": 60},
            "shuffle": {"questions": False, "options": False},
            "sections": [
                {
                    "id": str(uuid4()),
                    "title": None,
                    "instructions": None,
                    "duration_s": None,
                    "questions": [_question("NUMERICAL")],
                }
            ],
        }
    )
    .sections[0]
    .questions[0]
)
MSQ = (
    read_paper(
        {
            "title": "M",
            "timing": {"kind": "TOTAL", "allow_return": False, "total_duration_s": 60},
            "shuffle": {"questions": False, "options": False},
            "sections": [
                {
                    "id": str(uuid4()),
                    "title": None,
                    "instructions": None,
                    "duration_s": None,
                    "questions": [_question("MSQ")],
                }
            ],
        }
    )
    .sections[0]
    .questions[0]
)


def _choice(*ids: UUID) -> ChoiceAnswer:
    return ChoiceAnswer(frozenset(ids))


@pytest.mark.parametrize(
    ("answer", "question"),
    [
        (None, MCQ),
        (_choice(MCQ.option_ids[1]), MCQ),
        (_choice(), MCQ),
        (_choice(*MSQ.option_ids[:3]), MSQ),
        (NumericAnswer("-12.5"), NUMERICAL),
        (NumericAnswer("46"), NUMERICAL),
        (NumericAnswer("12345678.123456"), NUMERICAL),
    ],
)
def test_answers_that_fit(
    answer: ChoiceAnswer | NumericAnswer | None, question: PaperQuestion
) -> None:
    ensure_answer_fits(answer, question)


@pytest.mark.parametrize(
    ("answer", "question"),
    [
        (_choice(*MCQ.option_ids[:2]), MCQ),
        (_choice(uuid4()), MCQ),
        (_choice(MSQ.option_ids[0]), NUMERICAL),
        (NumericAnswer("12"), MCQ),
        (NumericAnswer("4e2"), NUMERICAL),
        (NumericAnswer(chr(0xFF11) + chr(0xFF12)), NUMERICAL),
        (NumericAnswer("12,5"), NUMERICAL),
        (NumericAnswer("123456789"), NUMERICAL),
        (NumericAnswer("1.1234567"), NUMERICAL),
        (NumericAnswer(".5"), NUMERICAL),
        (NumericAnswer(""), NUMERICAL),
    ],
)
def test_answers_that_dont_fit_e18(
    answer: ChoiceAnswer | NumericAnswer, question: PaperQuestion
) -> None:
    with pytest.raises(AnswerInvalid):
        ensure_answer_fits(answer, question)


@pytest.mark.parametrize(
    "answer", [None, NumericAnswer("-0.5"), _choice(*MSQ.option_ids[:2]), _choice()]
)
def test_answers_are_stored_and_read_back(answer: ChoiceAnswer | NumericAnswer | None) -> None:
    assert read_answer(answer_json(answer)) == answer
