from functools import lru_cache
from uuid import UUID

from core.rich_content import Json
from modules.assignments.repositories import papers


@lru_cache(maxsize=64)
def get_paper_content(assignment_id: UUID) -> Json:
    """The frozen paper, kept in memory: it never changes, and every exam-hall request reads
    it (database_schema.md §6). No policy: delivery asks only after its own checks. Treat the
    result as read-only, since every caller shares it."""
    return papers.content(assignment_id)
