from collections.abc import Callable, Sequence
from datetime import datetime
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Count, QuerySet

from core.db.locking import for_update
from core.errors import NotFound
from modules.students.domain.errors import GroupNameTaken
from modules.students.domain.values import GroupSummary
from modules.students.models import Group


def insert_group(*, name: str, normalized_name: str, description: str, now: datetime) -> UUID:
    group = Group(
        name=name,
        normalized_name=normalized_name,
        description=description,
        created_at=now,
        updated_at=now,
    )
    _with_unique_name(lambda: group.save(force_insert=True))
    return group.id


def get_group_for_update(group_id: UUID) -> Group:
    group = for_update(Group.objects.filter(pk=group_id)).first()
    if group is None:
        raise NotFound("group")
    return group


def update_group(
    group_id: UUID, *, name: str, normalized_name: str, description: str, now: datetime
) -> None:
    _with_unique_name(
        lambda: Group.objects.filter(pk=group_id).update(
            name=name, normalized_name=normalized_name, description=description, updated_at=now
        )
    )


def set_archived_at(group_id: UUID, archived_at: datetime | None, *, now: datetime) -> None:
    # Restoring can collide with an active group that took the name meanwhile
    _with_unique_name(
        lambda: Group.objects.filter(pk=group_id).update(archived_at=archived_at, updated_at=now)
    )


def get_group_summary(group_id: UUID) -> GroupSummary:
    found = _summaries(Group.objects.filter(pk=group_id))
    if not found:
        raise NotFound("group")
    return found[0]


def list_group_summaries(*, archived: bool, search: str | None) -> list[GroupSummary]:
    groups = Group.objects.filter(archived_at__isnull=not archived)
    if search:
        groups = groups.filter(name__icontains=search)
    return _summaries(groups.order_by("name", "id"))


def archived_by_id(group_ids: Sequence[UUID]) -> dict[UUID, bool]:
    """For the groups that exist: id → whether it is archived."""
    rows = Group.objects.filter(pk__in=group_ids).values_list("id", "archived_at")
    return {group_id: archived_at is not None for group_id, archived_at in rows}


def _summaries(groups: QuerySet[Group]) -> list[GroupSummary]:
    counted = groups.annotate(member_count=Count("memberships"))
    return [
        GroupSummary(
            id=group.id,
            name=group.name,
            description=group.description,
            archived_at=group.archived_at,
            member_count=group.member_count,
            created_at=group.created_at,
        )
        for group in counted
    ]


def _with_unique_name(write: Callable[[], object]) -> None:
    # Two groups racing for one name: the database's partial unique index decides
    try:
        with transaction.atomic():
            write()
    except IntegrityError:
        raise GroupNameTaken() from None
