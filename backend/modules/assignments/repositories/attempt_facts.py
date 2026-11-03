"""What the assignment use cases need to know about attempts: who has started, and how far
everyone has got. Attempts belong to delivery, which sits above assignments in the module
order, so they are read through the module named by the ATTEMPT_FACTS setting (ADR-074, the
same inversion as ADR-044)."""

from collections.abc import Sequence
from importlib import import_module
from typing import Protocol, cast
from uuid import UUID

from django.conf import settings

from modules.assignments.domain.assignment import Progress


class _AttemptFacts(Protocol):
    def students_with_attempts(self, assignment_id: UUID) -> set[UUID]: ...
    def attempt_counts(self, assignment_ids: Sequence[UUID]) -> dict[UUID, tuple[int, int]]: ...


def _reader() -> _AttemptFacts:
    return cast("_AttemptFacts", import_module(settings.ATTEMPT_FACTS))


def students_with_attempts(assignment_id: UUID) -> set[UUID]:
    return _reader().students_with_attempts(assignment_id)


def progress_by_assignment(assignment_ids: Sequence[UUID]) -> dict[UUID, Progress]:
    counts = _reader().attempt_counts(assignment_ids)
    return {
        assignment_id: Progress(*counts.get(assignment_id, (0, 0)))
        for assignment_id in assignment_ids
    }
