"""Section and tag scores, labels, question stats and the CSV (domain_model.md §6.4, §6.6)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from modules.results.domain.breakdown import (
    PartScore,
    attempt_label,
    section_scores,
    section_titles,
    tag_scores,
    time_taken_s,
)
from modules.results.domain.csv_export import BOM, csv_file_name, safe_cell, to_csv
from modules.results.domain.question_stats import question_stats

CELL, GENE = uuid4(), uuid4()


@dataclass(frozen=True)
class G:
    section_index: int
    marks_awarded: Decimal
    max_marks: Decimal
    tag_ids: tuple[UUID, ...] = ()


GRADES = [
    G(0, Decimal(4), Decimal(4), (CELL,)),
    G(0, Decimal(-1), Decimal(4), (CELL, GENE)),
    G(1, Decimal(2), Decimal(4), (GENE,)),
]


def test_section_scores_in_paper_order() -> None:
    assert section_scores(GRADES, ["Botany", None, "Empty"]) == [
        PartScore("Botany", Decimal(3), Decimal(8)),
        PartScore("Section 2", Decimal(2), Decimal(4)),
        PartScore("Empty", Decimal(0), Decimal(0)),
    ]
    assert section_titles({"sections": [{"title": "A"}, {"title": None}]}) == ["A", None]


def test_a_question_counts_for_each_of_its_tags() -> None:
    assert tag_scores(GRADES) == {CELL: (Decimal(3), Decimal(8)), GENE: (Decimal(1), Decimal(8))}


def test_label_and_time_taken() -> None:
    start = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)
    assert attempt_label("Cell Biology", start, 2) == "Cell Biology — 12 Nov 2026, 10:00 — Take 2"
    assert time_taken_s(start, start + timedelta(minutes=50)) == 3000
    assert time_taken_s(start, None) == 0


def test_question_stats_find_the_most_chosen_wrong_option() -> None:
    q, a, b, c = uuid4(), uuid4(), uuid4(), uuid4()
    key = {str(q): {"type": "MCQ", "correct_option_ids": [str(a)]}}
    outcomes = [(q, "CORRECT"), (q, "INCORRECT"), (q, "INCORRECT"), (q, "UNANSWERED")]
    picks = [(q, [a]), (q, [b]), (q, [b]), (q, [c])]

    stat = question_stats(outcomes, picks, key)[q]

    assert (stat.answered, stat.correct, stat.partial) == (3, 1, 0)
    assert (stat.top_wrong_option, stat.top_wrong_count) == (b, 2)
    numerical = question_stats([(c, "PARTIAL")], [], {})[c]
    assert (numerical.top_wrong_option, numerical.partial) == (None, 1)


def test_the_csv_is_safe_for_spreadsheets() -> None:
    assert safe_cell("=HYPERLINK(1)") == "'=HYPERLINK(1)"
    assert safe_cell("-1.00") == "-1.00"
    assert safe_cell("@SUM") == "'@SUM"
    assert safe_cell(None) == ""
    text = to_csv(["Name", "Score"], [["রিনা", "-1.00"], ["+cmd", 4]])
    assert text.startswith(BOM + "Name,Score\r\n")
    assert "রিনা,-1.00\r\n'+cmd,4\r\n" in text


def test_the_csv_file_name() -> None:
    assert (
        csv_file_name('Cell: "Biology"?', "2026-11-12")
        == "Cell Biology - 2026-11-12 - Gradebook.csv"
    )
    assert len(csv_file_name("x" * 400, "2026-11-12")) == 150
