from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.lifecycle import assignment_end
from modules.assignments.domain.live_controls import ensure_extension_valid
from modules.assignments.domain.paper_summary import paper_summary
from modules.assignments.repositories import audience, extensions
from modules.assignments.services.changes import lock_started
from modules.assignments.services.queries.get_paper_content import get_paper_content


def extend_time(  # keyword-only (CLAUDE.md limits)
    ctx: Ctx,
    *,
    assignment_id: UUID,
    seconds: int,
    student_ids: Sequence[UUID] | None,
    stage_index: int | None,
) -> datetime | None:
    """D-03 (domain_model.md §5.2, E-30): extra time for everyone (no students given) or the
    chosen ones, on one stage or the final one (None). It moves that stage's end and every
    later one; students see it on their next save or heartbeat. Returns when the test now
    ends for everyone (None for an open window)."""
    with transaction.atomic():
        record = lock_started(ctx, assignment_id)
        stages = len(paper_summary(get_paper_content(assignment_id)).stages)
        members = set(audience.member_ids(assignment_id))
        unknown = [s for s in student_ids or [] if s not in members]
        ensure_extension_valid(seconds, stage_index, stage_count=stages, unknown_students=unknown)
        chosen = None if student_ids is None else list(dict.fromkeys(student_ids))
        extensions.insert_extensions(
            assignment_id, student_ids=chosen, stage_index=stage_index, seconds=seconds, now=ctx.now
        )
        grants = extensions.grants_by_assignment([assignment_id]).get(assignment_id, [])
    return assignment_end(record.timeline, grants)
