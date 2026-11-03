"""Groups and who is in them (domain_model.md §3.2 Group, GroupMembership, PerformanceShare)."""

from collections.abc import Collection, Mapping, Sequence
from uuid import UUID

from core.bulk import BulkOutcome
from core.context import StudentStatus
from core.text import clean_text_line
from modules.students.domain.bulk import plan, unless_admitted


def normalize_group_name(name: str) -> str:
    """'Class 11 A' and 'class  11 a' are the same name: names are unique case-insensitively."""
    return clean_text_line(name).casefold()


def plan_adding_members(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus], members: Collection[UUID]
) -> BulkOutcome:
    """Only admitted (ACTIVE or DEACTIVATED) students can be members (§3.2 #1)."""
    return plan(
        requested,
        statuses,
        lambda student_id, status: (
            unless_admitted(status) or ("already_member" if student_id in members else None)
        ),
    )


def plan_removing_members(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus], members: Collection[UUID]
) -> BulkOutcome:
    return plan(
        requested,
        statuses,
        lambda student_id, _status: None if student_id in members else "not_member",
    )


def plan_sharing(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus], shared: Collection[UUID]
) -> BulkOutcome:
    """Performance is shared with admitted students only; sharing twice changes nothing."""
    return plan(
        requested,
        statuses,
        lambda student_id, status: (
            unless_admitted(status) or ("already_shared" if student_id in shared else None)
        ),
    )


def plan_unsharing(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus], shared: Collection[UUID]
) -> BulkOutcome:
    return plan(
        requested,
        statuses,
        lambda student_id, _status: None if student_id in shared else "not_shared",
    )
