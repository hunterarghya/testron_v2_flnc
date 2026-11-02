"""How much each tag is used (by questions, and by tests through their questions), and the
question references a merge moves or a delete removes (ADR-059)."""

from collections.abc import Sequence
from uuid import UUID

from django.db.models import Count

from modules.authoring.models import QuestionTag


def question_counts(tag_ids: Sequence[UUID]) -> dict[UUID, int]:
    counts = dict.fromkeys(tag_ids, 0)
    rows = (
        QuestionTag.objects.filter(tag_id__in=tag_ids)
        .values("tag_id")
        .annotate(n=Count("question_id"))
        .values_list("tag_id", "n")
    )
    counts.update(rows)
    return counts


def test_counts(tag_ids: Sequence[UUID]) -> dict[UUID, int]:
    counts = dict.fromkeys(tag_ids, 0)
    rows = (
        QuestionTag.objects.filter(tag_id__in=tag_ids)
        .values("tag_id")
        .annotate(n=Count("question__test_id", distinct=True))
        .values_list("tag_id", "n")
    )
    counts.update(rows)
    return counts


def move_references(from_tag_id: UUID, to_tag_id: UUID) -> None:
    """Point every question tagged `from` at `to` instead (a merge). A question that already
    has both keeps one."""
    question_ids = list(
        QuestionTag.objects.filter(tag_id=from_tag_id).values_list("question_id", flat=True)
    )
    QuestionTag.objects.bulk_create(
        [QuestionTag(question_id=qid, tag_id=to_tag_id) for qid in question_ids],
        ignore_conflicts=True,
    )
    QuestionTag.objects.filter(tag_id=from_tag_id).delete()


def remove_references(tag_id: UUID) -> int:
    """Untag every question; how many questions had it."""
    removed, _ = QuestionTag.objects.filter(tag_id=tag_id).delete()
    return removed
