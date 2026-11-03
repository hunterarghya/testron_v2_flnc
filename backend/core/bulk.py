"""The result of a bulk action on students: each requested student is applied or skipped
with a reason, never refused as a whole (domain_model.md §3.2 #4). Plain Python: any
module's domain may use it."""

from dataclasses import dataclass
from uuid import UUID

NOT_FOUND = "not_found"


@dataclass(frozen=True, slots=True)
class Skip:
    student_id: UUID
    # "not_found", "status_<status>", or what made the change pointless ("already_member", …)
    reason: str


@dataclass(frozen=True, slots=True)
class BulkOutcome:
    applied: tuple[UUID, ...]
    skipped: tuple[Skip, ...]
