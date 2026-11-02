"""The only names other modules may import from students (R-08)."""

from modules.students.services.queries.count_pending_students import count_pending_students

__all__ = ["count_pending_students"]
