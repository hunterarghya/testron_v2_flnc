"""Counts and ids about attempts that screens outside the exam hall need: My Tests and the
gate here, and the assignment screens through `public.py` (ADR-074)."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from django.db.models import Count, Q

from modules.delivery.domain.gate import Sittings
from modules.delivery.domain.values import AttemptStatus
from modules.delivery.models import Attempt

_RUNNING = Q(status=AttemptStatus.IN_PROGRESS)


def sittings_by_assignment(
    student_id: UUID, assignment_ids: Sequence[UUID]
) -> dict[UUID, Sittings]:
    found: dict[UUID, Sittings] = defaultdict(Sittings)
    rows = Attempt.objects.filter(
        student_id=student_id, assignment_id__in=assignment_ids
    ).values_list("assignment_id", "id", "status")
    for assignment_id, attempt_id, status in rows:
        sittings = found[assignment_id]
        running = attempt_id if status == AttemptStatus.IN_PROGRESS else None
        found[assignment_id] = replace(
            sittings,
            used=sittings.used + 1,
            in_progress_attempt_id=running or sittings.in_progress_attempt_id,
        )
    return {assignment_id: found[assignment_id] for assignment_id in assignment_ids}


def students_with_attempts(assignment_id: UUID) -> set[UUID]:
    rows = Attempt.objects.filter(assignment_id=assignment_id).values_list("student_id", flat=True)
    return set(rows)


def counts_by_assignment(assignment_ids: Sequence[UUID]) -> dict[UUID, tuple[int, int]]:
    """(ended, in progress) per assignment, in one query."""
    rows = (
        Attempt.objects.filter(assignment_id__in=assignment_ids)
        .values("assignment_id")
        .annotate(running=Count("id", filter=_RUNNING), ended=Count("id", filter=~_RUNNING))
        .values_list("assignment_id", "ended", "running")
    )
    return {assignment_id: (ended, running) for assignment_id, ended, running in rows}
