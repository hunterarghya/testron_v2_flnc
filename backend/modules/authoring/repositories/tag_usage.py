"""How much each tag is used: by questions, and by tests through their questions.

The question references (`question_tags`) arrive with the authoring models in step 3.2;
until then no tag is used anywhere (backlog B-11).
"""

from collections.abc import Sequence
from uuid import UUID


def question_counts(tag_ids: Sequence[UUID]) -> dict[UUID, int]:
    return dict.fromkeys(tag_ids, 0)


def test_counts(tag_ids: Sequence[UUID]) -> dict[UUID, int]:
    return dict.fromkeys(tag_ids, 0)


def move_references(from_tag_id: UUID, to_tag_id: UUID) -> None:
    """Point every question tagged `from` at `to` instead (a merge). Nothing to move yet."""


def remove_references(tag_id: UUID) -> int:
    """Untag every question; how many questions had it. Nothing to remove yet."""
    return 0
