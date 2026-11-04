"""The correction history in the teacher's words (T-11)."""

from modules.results.domain.key_history import EntryText, entry_text, numbered_questions

MSQ = {"id": "q2", "type": "MSQ", "options": [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}]}
PAPER = {"sections": [{"questions": [{"id": "q1", "type": "NUMERICAL"}]}, {"questions": [MSQ]}]}


def test_questions_are_numbered_across_sections() -> None:
    numbered = numbered_questions(PAPER)
    assert {qid: n for qid, (n, _) in numbered.items()} == {"q1": 1, "q2": 2}


def test_options_read_as_letters_in_order_and_numbers_with_their_tolerance() -> None:
    assert entry_text(MSQ, {"correct_option_ids": ["o3", "o1"]}) == EntryText(labels=("A", "C"))
    assert entry_text(MSQ, {"correct_option_ids": ["gone"]}) == EntryText()
    numerical = entry_text({"type": "NUMERICAL"}, {"answer": "46.5", "tolerance": "0.5"})
    assert numerical == EntryText(answer="46.5", tolerance="0.5")
