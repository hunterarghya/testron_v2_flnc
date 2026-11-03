from collections.abc import Sequence
from uuid import UUID

from modules.students.domain.values import StudentBrief
from modules.students.repositories import memberships, students


def describe_students(student_ids: Sequence[UUID]) -> list[StudentBrief]:
    """The students among these ids, in the order given, with their status and active
    groups. Two queries. No policy here: callers are other modules' use cases, which check
    the teacher first."""
    found = students.names_and_statuses(student_ids)
    groups = memberships.group_names_by_student(list(found))
    return [
        StudentBrief(sid, *found[sid], group_names=groups[sid])
        for sid in dict.fromkeys(student_ids)
        if sid in found
    ]
