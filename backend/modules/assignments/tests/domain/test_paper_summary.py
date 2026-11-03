"""What students are told about a paper before starting (P-01, P-02)."""

from decimal import Decimal

from modules.assignments.domain.paper_summary import Stage, paper_summary


def question(
    marks: str = "4.00", negative: str = "1.00", time_s: int | None = None
) -> dict[str, object]:
    return {"id": "q", "marks": marks, "negative_marks": negative, "time_s": time_s}


def paper(
    kind: str, sections: list[dict[str, object]], *, allow_return: bool = True
) -> dict[str, object]:
    return {
        "timing": {"kind": kind, "allow_return": allow_return, "total_duration_s": 1800},
        "sections": sections,
    }


def test_a_total_paper_is_one_stage_with_uniform_marking() -> None:
    summary = paper_summary(
        paper("TOTAL", [{"title": None, "duration_s": None, "questions": [question(), question()]}])
    )

    assert (summary.question_count, summary.total_marks) == (2, Decimal(8))
    assert summary.stages == (Stage(None, 1800),)
    assert summary.marking == (Decimal(4), Decimal(1))


def test_sections_are_stages_and_mixed_marks_say_so() -> None:
    sections = [
        {"title": "Botany", "duration_s": 600, "questions": [question()]},
        {"title": "Zoology", "duration_s": 1200, "questions": [question("2.00", "0.00")]},
    ]

    summary = paper_summary(paper("SECTIONED", sections))

    assert summary.stages == (Stage("Botany", 600), Stage("Zoology", 1200))
    assert (summary.marking, summary.allow_return) == (None, True)


def test_rapid_fire_has_a_stage_per_question_and_never_goes_back() -> None:
    questions = [question(time_s=30), question(time_s=45)]

    summary = paper_summary(
        paper("PER_QUESTION", [{"title": None, "duration_s": None, "questions": questions}])
    )

    assert summary.stages == (Stage(None, 30), Stage(None, 45))
    assert summary.allow_return is False
