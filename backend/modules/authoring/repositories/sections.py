"""Sections, and where every question sits: the test's layout (sections in order, each with
its questions in order). Positions are rewritten whole; the uniques are checked at commit."""

from collections.abc import Sequence
from uuid import UUID

from modules.authoring.domain.structure import Layout
from modules.authoring.models import Question, Section


def insert_section(test_id: UUID, *, position: int, title: str, duration_s: int | None) -> UUID:
    return Section.objects.create(
        test_id=test_id, position=position, title=title, duration_s=duration_s
    ).id


def update_section(section_id: UUID, values: dict[str, object]) -> None:
    Section.objects.filter(pk=section_id).update(**values)


def delete_section(section_id: UUID) -> None:
    Section.objects.filter(pk=section_id).delete()


def delete_sections(section_ids: Sequence[UUID]) -> None:
    Section.objects.filter(pk__in=section_ids).delete()


def section_order(test_id: UUID) -> list[UUID]:
    return list(
        Section.objects.filter(test_id=test_id).order_by("position").values_list("id", flat=True)
    )


def layout(test_id: UUID) -> list[tuple[UUID, list[UUID]]]:
    """Sections in order, each with its question ids in order (two queries)."""
    found: dict[UUID, list[UUID]] = {section_id: [] for section_id in section_order(test_id)}
    rows = (
        Question.objects.filter(test_id=test_id)
        .order_by("position")
        .values_list("section_id", "id")
    )
    for section_id, question_id in rows:
        found[section_id].append(question_id)
    return list(found.items())


def apply_layout(wanted: Layout) -> None:
    """Write every section's position and every question's section and position."""
    Section.objects.bulk_update(
        [
            Section(id=section_id, position=position)
            for position, (section_id, _) in enumerate(wanted)
        ],
        ["position"],
    )
    placed = [
        Question(id=question_id, section_id=section_id, position=position)
        for section_id, questions in wanted
        for position, question_id in enumerate(questions)
    ]
    Question.objects.bulk_update(placed, ["section_id", "position"])
