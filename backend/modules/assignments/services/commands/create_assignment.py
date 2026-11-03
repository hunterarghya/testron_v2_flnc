from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.assignment import Settings, checked_settings
from modules.assignments.domain.settings import content_hash
from modules.assignments.domain.window import ensure_window_valid
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments, audience, papers
from modules.assignments.services.inputs import active_audience, password_token
from modules.assignments.services.views import AssignmentDetail, assignment_detail
from modules.authoring import public as authoring


@dataclass(frozen=True, slots=True)
class NewAssignment:
    """The wizard's answers (T-07)."""

    test_id: UUID
    settings: Settings
    student_ids: Sequence[UUID]
    timing_override: authoring.TimingOverride | None = None
    password: str | None = None
    password_confirm: str | None = None
    # The groups the students were picked from (ADR-071)
    source_group_ids: Sequence[UUID] = ()


def create_assignment(ctx: Ctx, *, new: NewAssignment) -> AssignmentDetail:
    """Give a test to the chosen students (domain_model.md §3.5 #1-4): a test without
    problems, at least one ACTIVE student, a valid window. The paper, answer key and audience
    are written with the assignment, in one transaction."""
    ensure_teacher(ctx.actor)
    settings = checked_settings(new.settings)
    student_ids = active_audience(new.student_ids)
    token = password_token(new.password, new.password_confirm)
    with transaction.atomic():
        frozen = authoring.freeze_test(new.test_id, override=new.timing_override, now=ctx.now)
        ensure_window_valid(settings.window, now=ctx.now, total_duration_s=frozen.total_duration_s)
        assignment_id = assignments.insert_assignment(
            settings,
            test_id=new.test_id,
            timing_kind=frozen.timing_kind.value,
            total_duration_s=frozen.total_duration_s,
            password_token=token,
            now=ctx.now,
        )
        papers.insert_paper(
            assignment_id,
            content=frozen.paper,
            content_hash=content_hash(frozen.paper),
            key_entries=frozen.key_entries,
            solutions=frozen.solutions,
            now=ctx.now,
        )
        audience.add_members(assignment_id, student_ids, now=ctx.now)
        assignments.set_source_groups(assignment_id, list(dict.fromkeys(new.source_group_ids)))
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
