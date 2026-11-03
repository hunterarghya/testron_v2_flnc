from datetime import datetime
from uuid import UUID

from modules.authoring.domain.freeze import FrozenTest, TimingOverride, freeze
from modules.authoring.repositories import tests_table
from modules.authoring.services.editing import read_document


def freeze_test(test_id: UUID, *, override: TimingOverride | None, now: datetime) -> FrozenTest:
    """The test as a paper and answer key, for a new assignment (domain_model.md §3.5 #2,
    §4.3), and the library's "last assigned" date. Runs inside the caller's transaction. No
    policy here: the caller is the assignments use case, which checks the teacher first."""
    frozen = freeze(read_document(test_id), override)
    tests_table.update_test(test_id, {"last_assigned_at": now})
    return frozen
