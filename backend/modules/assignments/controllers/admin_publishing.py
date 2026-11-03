from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.assignments.domain.publishing import PublicationChanges
from modules.assignments.dto.publishing import PublicationPatchIn, PublishIn
from modules.assignments.dto.views import AssignmentDetailOut, PublicationOut
from modules.assignments.services.commands import publish_results as publishing
from modules.assignments.services.commands import unpublish_results as unpublishing
from modules.assignments.services.commands import update_publication as updating


def publish_results(
    request: HttpRequest, assignment_id: UUID, payload: PublishIn
) -> PublicationOut:
    changes = payload.options.to_changes() if payload.options else PublicationChanges()
    detail = publishing.publish_results(
        ctx_from(request), assignment_id=assignment_id, changes=changes
    )
    return AssignmentDetailOut.from_detail(detail).publication


def unpublish_results(request: HttpRequest, assignment_id: UUID) -> PublicationOut:
    detail = unpublishing.unpublish_results(ctx_from(request), assignment_id=assignment_id)
    return AssignmentDetailOut.from_detail(detail).publication


def update_publication(
    request: HttpRequest, assignment_id: UUID, payload: PublicationPatchIn
) -> PublicationOut:
    detail = updating.update_publication(
        ctx_from(request), assignment_id=assignment_id, changes=payload.to_changes()
    )
    return AssignmentDetailOut.from_detail(detail).publication
