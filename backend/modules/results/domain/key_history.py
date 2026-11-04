"""The answer key's correction history in the teacher's words (T-11, security.md T-05):
"Q3: B → C", or "46 ± 0 → 46.5 ± 0.5" for a numerical question."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

Json = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class EntryText:
    """MCQ/MSQ: the options' letters as students saw them in the teacher's order (A, B, …).
    Numerical: the answer and its tolerance."""

    labels: tuple[str, ...] = ()
    answer: str | None = None
    tolerance: str | None = None


def numbered_questions(paper: Json) -> dict[str, tuple[int, Json]]:
    """Each question id with its number in the paper (1, 2, … across sections)."""
    questions = [
        q
        for s in cast("Sequence[Json]", paper["sections"])
        for q in cast("Sequence[Json]", s["questions"])
    ]
    return {str(q["id"]): (n, q) for n, q in enumerate(questions, start=1)}


def entry_text(question: Json, entry: Json) -> EntryText:
    if "answer" in entry:
        return EntryText(answer=str(entry["answer"]), tolerance=str(entry.get("tolerance", "0")))
    letters = {
        str(o["id"]): chr(ord("A") + i)
        for i, o in enumerate(cast("Sequence[Json]", question.get("options", [])))
    }
    picked = cast("Sequence[str]", entry.get("correct_option_ids", []))
    return EntryText(labels=tuple(sorted(letters[o] for o in picked if o in letters)))
