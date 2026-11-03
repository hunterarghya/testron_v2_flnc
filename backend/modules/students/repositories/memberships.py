from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from django.db.models import F

from core.context import StudentStatus
from modules.students.domain.values import AudienceCandidate, GroupMember, GroupRef, GroupRoster
from modules.students.models import Group, GroupMembership, PerformanceShare, Student


def member_ids(group_id: UUID) -> set[UUID]:
    return set(
        GroupMembership.objects.filter(group_id=group_id).values_list("student_id", flat=True)
    )


def add_members(group_id: UUID, student_ids: Sequence[UUID], *, now: datetime) -> None:
    GroupMembership.objects.bulk_create(
        [GroupMembership(group_id=group_id, student_id=sid, added_at=now) for sid in student_ids],
        ignore_conflicts=True,
    )


def remove_members(group_id: UUID, student_ids: Sequence[UUID]) -> None:
    GroupMembership.objects.filter(group_id=group_id, student_id__in=student_ids).delete()


def remove_from_all_groups(student_id: UUID) -> None:
    GroupMembership.objects.filter(student_id=student_id).delete()


def list_members(group_id: UUID) -> list[GroupMember]:
    """The group's students by name, with what T-17 shows about each (one query)."""
    rows = (
        GroupMembership.objects.filter(group_id=group_id)
        .order_by("student__user__name", "student_id")
        .values(
            "student_id",
            "added_at",
            name=F("student__user__name"),
            email=F("student__user__email"),
            status=F("student__status"),
        )
    )
    shared = set(
        PerformanceShare.objects.filter(student__memberships__group_id=group_id).values_list(
            "student_id", flat=True
        )
    )
    return [
        GroupMember(
            id=row["student_id"],
            name=row["name"],
            email=row["email"],
            status=StudentStatus(row["status"]),
            added_at=row["added_at"],
            performance_shared=row["student_id"] in shared,
        )
        for row in rows
    ]


def group_names_by_student(student_ids: Sequence[UUID]) -> dict[UUID, list[str]]:
    """Each student's active groups, by name (archived groups are out of sight)."""
    names: dict[UUID, list[str]] = {sid: [] for sid in student_ids}
    rows = (
        GroupMembership.objects.filter(student_id__in=student_ids, group__archived_at__isnull=True)
        .order_by("group__name")
        .values_list("student_id", "group__name")
    )
    for student_id, name in rows:
        names[student_id].append(name)
    return names


def groups_of_student(student_id: UUID) -> list[GroupRef]:
    """The student's active groups, by name."""
    rows = (
        GroupMembership.objects.filter(student_id=student_id, group__archived_at__isnull=True)
        .order_by("group__name")
        .values_list("group_id", "group__name")
    )
    return [GroupRef(id=group_id, name=name) for group_id, name in rows]


def active_students_in_groups(group_ids: Sequence[UUID]) -> list[AudienceCandidate]:
    """ACTIVE members of any of the groups, each once, with all their matching groups."""
    rows = (
        Student.objects.filter(status=StudentStatus.ACTIVE, memberships__group_id__in=group_ids)
        .order_by("user__name", "user_id")
        .values_list("user_id", "user__name", "user__email", "memberships__group__name")
    )
    candidates: dict[UUID, AudienceCandidate] = {}
    for student_id, name, email, group_name in rows:
        candidate = candidates.setdefault(
            student_id, AudienceCandidate(student_id, name, email, [])
        )
        candidate.group_names.append(group_name)
    return list(candidates.values())


def rosters(group_ids: Sequence[UUID]) -> list[GroupRoster]:
    """The groups, by name, each with its ACTIVE members. Two queries."""
    groups = Group.objects.filter(pk__in=group_ids).order_by("name").values_list("id", "name")
    members: dict[UUID, set[UUID]] = {gid: set() for gid in group_ids}
    rows = GroupMembership.objects.filter(
        group_id__in=group_ids, student__status=StudentStatus.ACTIVE
    ).values_list("group_id", "student_id")
    for group_id, student_id in rows:
        members[group_id].add(student_id)
    return [GroupRoster(gid, name, frozenset(members[gid])) for gid, name in groups]
