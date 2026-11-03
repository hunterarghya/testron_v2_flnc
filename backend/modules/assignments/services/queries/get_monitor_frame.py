from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.context import Ctx
from modules.assignments.domain.entry import entry_window
from modules.assignments.domain.lifecycle import ExtensionGrant
from modules.assignments.domain.paper_summary import paper_summary
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments, audience, extensions
from modules.assignments.services.queries.get_paper_content import get_paper_content
from modules.assignments.services.queries.get_sitting_terms import SittingTerms
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class MonitorMember:
    student_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class MonitorFrame:
    """The assignment's side of the live monitor (T-10): who sits it and its time limits."""

    assignment_id: UUID
    title: str
    members: tuple[MonitorMember, ...]
    question_count: int
    # When the test ends for everyone; None for an open window or before the start
    ends_at: datetime | None
    everyone: SittingTerms
    by_student: dict[UUID, SittingTerms]

    def terms_for(self, student_id: UUID) -> SittingTerms:
        return self.by_student.get(student_id, self.everyone)


def get_monitor_frame(ctx: Ctx, *, assignment_id: UUID) -> MonitorFrame:
    """For delivery's monitor, in five queries however many students there are."""
    ensure_teacher(ctx.actor)
    record = assignments.get_record(assignment_id)
    grants = extensions.by_student(assignment_id)
    shared = grants.get(None, [])
    members = students.describe_students(audience.member_ids(assignment_id))
    settings = record.settings

    def terms(own: list[ExtensionGrant]) -> SittingTerms:
        return SittingTerms(
            settings.title,
            settings.window,
            record.timeline.ended_at,
            (*shared, *own),
            settings.integrity,
        )

    return MonitorFrame(
        assignment_id=assignment_id,
        title=settings.title,
        members=tuple(MonitorMember(m.student_id, m.name) for m in members),
        question_count=paper_summary(get_paper_content(assignment_id)).question_count,
        ends_at=entry_window(record.timeline, shared).ends_at,
        everyone=terms([]),
        by_student={s: terms(own) for s, own in grants.items() if s is not None},
    )
