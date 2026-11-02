from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Status

from core.http.context import ctx_from
from modules.students.dto.groups import (
    AudienceCandidateOut,
    AudiencePreviewIn,
    GroupDetailOut,
    GroupFilterIn,
    GroupIn,
    GroupOut,
    GroupPatchIn,
)
from modules.students.dto.students import BulkResultOut, ShareIn, StudentIdsIn
from modules.students.services.commands import add_group_members as adding
from modules.students.services.commands import archive_group as archiving
from modules.students.services.commands import create_group as creating
from modules.students.services.commands import remove_group_members as removing
from modules.students.services.commands import restore_group as restoring
from modules.students.services.commands import share_performance as sharing
from modules.students.services.commands import unshare_performance as unsharing
from modules.students.services.commands import update_group as updating
from modules.students.services.queries import get_group as detail
from modules.students.services.queries import list_groups as listing
from modules.students.services.queries import preview_audience as preview


def list_groups(request: HttpRequest, filters: Query[GroupFilterIn]) -> list[GroupOut]:
    groups = listing.list_groups(ctx_from(request), archived=filters.archived, search=filters.q)
    return [GroupOut.from_summary(group) for group in groups]


def create_group(request: HttpRequest, payload: GroupIn) -> Status[GroupOut]:
    group = creating.create_group(
        ctx_from(request), name=payload.name, description=payload.description
    )
    return Status(201, GroupOut.from_summary(group))


def get_group(request: HttpRequest, group_id: UUID) -> GroupDetailOut:
    return GroupDetailOut.from_detail(detail.get_group(ctx_from(request), group_id=group_id))


def update_group(request: HttpRequest, group_id: UUID, payload: GroupPatchIn) -> GroupOut:
    group = updating.update_group(
        ctx_from(request), group_id=group_id, name=payload.name, description=payload.description
    )
    return GroupOut.from_summary(group)


def archive_group(request: HttpRequest, group_id: UUID) -> GroupOut:
    return GroupOut.from_summary(archiving.archive_group(ctx_from(request), group_id=group_id))


def restore_group(request: HttpRequest, group_id: UUID) -> GroupOut:
    return GroupOut.from_summary(restoring.restore_group(ctx_from(request), group_id=group_id))


def add_group_members(request: HttpRequest, group_id: UUID, payload: StudentIdsIn) -> BulkResultOut:
    outcome = adding.add_group_members(
        ctx_from(request), group_id=group_id, student_ids=payload.student_ids
    )
    return BulkResultOut.from_outcome(outcome)


def remove_group_members(
    request: HttpRequest, group_id: UUID, payload: StudentIdsIn
) -> BulkResultOut:
    outcome = removing.remove_group_members(
        ctx_from(request), group_id=group_id, student_ids=payload.student_ids
    )
    return BulkResultOut.from_outcome(outcome)


def preview_audience(
    request: HttpRequest, filters: Query[AudiencePreviewIn]
) -> list[AudienceCandidateOut]:
    candidates = preview.preview_audience(ctx_from(request), group_ids=filters.group_ids)
    return [AudienceCandidateOut.from_candidate(candidate) for candidate in candidates]


def share_performance(request: HttpRequest, payload: ShareIn) -> BulkResultOut:
    outcome = sharing.share_performance(
        ctx_from(request), student_ids=payload.student_ids, group_id=payload.group_id
    )
    return BulkResultOut.from_outcome(outcome)


def unshare_performance(request: HttpRequest, payload: StudentIdsIn) -> BulkResultOut:
    outcome = unsharing.unshare_performance(ctx_from(request), student_ids=payload.student_ids)
    return BulkResultOut.from_outcome(outcome)
