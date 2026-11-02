"""A test's shape: positions, reorders and the timing-mode switch (domain_model.md §3.4,
structural invariants 1-2, T-04)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from uuid import UUID

from core.errors import FieldError, FieldsInvalid
from modules.authoring.domain.drafts import Timing
from modules.authoring.domain.values import TimingKind

# What a new or switched timing starts with (domain_model.md §3.4 defaults)
DEFAULT_DURATION_S = 3600
DEFAULT_QUESTION_S = 60
MIN_TOTAL_S = 60

# Sections in order, each with its questions in order
Layout = Sequence[tuple[UUID, Sequence[UUID]]]


def insert_after(ids: Sequence[UUID], new_id: UUID, after_id: UUID | None) -> list[UUID]:
    """`ids` with `new_id` placed right after `after_id`; None puts it first."""
    if after_id is None:
        return [new_id, *ids]
    if after_id not in ids:
        raise FieldsInvalid(FieldError("after_id", "not_found", "That item is not here"))
    cut = list(ids).index(after_id) + 1
    return [*ids[:cut], new_id, *ids[cut:]]


def positions(ids: Sequence[UUID]) -> dict[UUID, int]:
    """Dense positions 0..n-1 in list order (invariant 2)."""
    return {item: position for position, item in enumerate(ids)}


def ensure_same_structure(current: Layout, wanted: Layout) -> None:
    """A reorder may move sections and questions anywhere, but must name exactly the test's
    sections and questions, each once (api_contract.md §2.5, PUT …/structure)."""
    if _sorted_ids(s for s, _ in wanted) != _sorted_ids(s for s, _ in current):
        raise FieldsInvalid(FieldError("sections", "mismatch", "List every section exactly once"))
    wanted_questions = _sorted_ids(q for _, questions in wanted for q in questions)
    if wanted_questions != _sorted_ids(q for _, questions in current for q in questions):
        raise FieldsInvalid(FieldError("sections", "mismatch", "List every question exactly once"))


def _sorted_ids(ids: Iterable[UUID]) -> list[UUID]:
    return sorted(ids)


def merged(layout: Layout) -> Layout:
    """Every question in the first section, order kept (switching away from SECTIONED)."""
    if not layout:
        return []
    first_id = layout[0][0]
    return [(first_id, [q for _, questions in layout for q in questions])]


@dataclass(frozen=True, slots=True)
class TimingSwitch:
    timing: Timing
    # Leaving SECTIONED: one section remains, with every question
    merge_sections: bool
    # Entering SECTIONED from TOTAL: the old duration, for a section that has none yet
    section_duration_s: int | None


def switch_timing(
    current: Timing, kind: TimingKind, *, section_durations: Sequence[int | None]
) -> TimingSwitch:
    """The new timing and what it does to sections. Same kind: nothing changes."""
    if kind is current.kind:
        return TimingSwitch(current, merge_sections=False, section_duration_s=None)
    leaving_sections = current.kind is TimingKind.SECTIONED
    if kind is TimingKind.TOTAL:
        timing = Timing(
            kind,
            duration_s=_total_of(section_durations) if leaving_sections else DEFAULT_DURATION_S,
        )
    elif kind is TimingKind.PER_QUESTION:
        timing = Timing(kind, default_question_s=DEFAULT_QUESTION_S)
    else:
        timing = Timing(kind, allow_return=False)
    carried = current.duration_s if kind is TimingKind.SECTIONED else None
    return TimingSwitch(timing, merge_sections=leaving_sections, section_duration_s=carried)


def _total_of(durations: Sequence[int | None]) -> int:
    """The sections' time added up, when every section has one; else the default."""
    known = [d for d in durations if d is not None]
    if len(known) == len(durations) and sum(known) >= MIN_TOTAL_S:
        return sum(known)
    return DEFAULT_DURATION_S
