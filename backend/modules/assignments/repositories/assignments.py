from collections.abc import Collection, Sequence
from datetime import datetime
from uuid import UUID

from django.db.models import Q, QuerySet
from django.db.models.functions import Coalesce

from core.db.locking import for_update
from core.errors import NotFound
from modules.assignments.domain.assignment import AssignmentRecord, Settings
from modules.assignments.domain.settings import Publication
from modules.assignments.models import Assignment
from modules.assignments.repositories.columns import (
    publication_columns,
    record_of,
    settings_columns,
)


def insert_assignment(
    settings: Settings,
    *,
    test_id: UUID,
    timing_kind: str,
    total_duration_s: int,
    password_token: str | None,
    now: datetime,
) -> UUID:
    row = Assignment.objects.create(
        test_id=test_id,
        timing_kind=timing_kind,
        total_duration_s=total_duration_s,
        password_ciphertext=password_token,
        created_at=now,
        updated_at=now,
        **settings_columns(settings),
    )
    return row.id


def get_record(assignment_id: UUID) -> AssignmentRecord:
    return record_of(_one(Assignment.objects.all(), assignment_id))


def lock_record(assignment_id: UUID) -> AssignmentRecord:
    """Locked until the use case's transaction ends: one change at a time."""
    return record_of(_one(for_update(Assignment.objects.all()), assignment_id))


def list_records(
    *,
    search: str | None,
    student_ids: Collection[UUID] | None,
    between: tuple[datetime | None, datetime | None],
) -> list[AssignmentRecord]:
    """Newest first. `between` filters on when it happens: its start, opening or plan, else
    when it was made."""
    rows = Assignment.objects.annotate(
        happens_at=Coalesce("starts_at", "opens_at", "planned_at", "activated_at", "created_at")
    ).order_by("-created_at", "-id")
    if search:
        rows = rows.filter(title__icontains=search)
    if student_ids is not None:
        rows = rows.filter(audience__student_id__in=student_ids).distinct()
    start, end = between
    rows = rows.filter(Q(happens_at__gte=start) if start else Q()).filter(
        Q(happens_at__lt=end) if end else Q()
    )
    return [record_of(row) for row in rows]


def update_settings(assignment_id: UUID, settings: Settings, *, now: datetime) -> None:
    Assignment.objects.filter(pk=assignment_id).update(**settings_columns(settings), updated_at=now)


def get_password_token(assignment_id: UUID) -> str | None:
    tokens = Assignment.objects.filter(pk=assignment_id).values_list("password_ciphertext")
    found = tokens.first()
    if found is None:
        raise NotFound("assignment")
    return found[0]


def set_password_token(assignment_id: UUID, token: str | None, *, now: datetime) -> None:
    Assignment.objects.filter(pk=assignment_id).update(password_ciphertext=token, updated_at=now)


def mark_cancelled(assignment_id: UUID, *, now: datetime) -> None:
    Assignment.objects.filter(pk=assignment_id).update(cancelled_at=now, updated_at=now)


def _one(rows: QuerySet[Assignment], assignment_id: UUID) -> Assignment:
    row = rows.filter(pk=assignment_id).first()
    if row is None:
        raise NotFound("assignment")
    return row


def set_source_groups(assignment_id: UUID, group_ids: Sequence[UUID]) -> None:
    Assignment.objects.filter(pk=assignment_id).update(source_group_ids=list(group_ids))


def mark_activated(assignment_id: UUID, *, now: datetime) -> None:
    Assignment.objects.filter(pk=assignment_id).update(activated_at=now, updated_at=now)


def list_records_for_student(student_id: UUID) -> list[AssignmentRecord]:
    """Every assignment the student is in, not cancelled (A-01), newest first."""
    rows = Assignment.objects.filter(
        audience__student_id=student_id, cancelled_at__isnull=True
    ).order_by("-created_at", "-id")
    return [record_of(row) for row in rows]


def get_record_for_student(assignment_id: UUID, student_id: UUID) -> AssignmentRecord:
    """Not in the audience, cancelled or missing all look the same (A-02)."""
    rows = Assignment.objects.filter(audience__student_id=student_id, cancelled_at__isnull=True)
    return record_of(_one(rows, assignment_id))


def mark_ended(assignment_id: UUID, *, now: datetime) -> None:
    """ "End for everyone": the first time only, so ending twice keeps the first instant."""
    Assignment.objects.filter(pk=assignment_id, ended_at__isnull=True).update(
        ended_at=now, updated_at=now
    )


def set_publication(
    assignment_id: UUID, publication: Publication, *, published_at: datetime | None, now: datetime
) -> None:
    """The results settings and when they were published (None: not, or unpublished)."""
    Assignment.objects.filter(pk=assignment_id).update(
        **publication_columns(publication), published_at=published_at, updated_at=now
    )
