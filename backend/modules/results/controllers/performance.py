from uuid import UUID

from django.http import HttpRequest

from core.http.context import ctx_from
from modules.results.dto.performance import GroupPerformanceOut, PerformanceOut
from modules.results.services.queries import get_group_performance as group
from modules.results.services.queries import get_my_performance as mine
from modules.results.services.queries import get_student_performance as student


def get_my_performance(request: HttpRequest) -> PerformanceOut:
    return PerformanceOut.from_view(mine.get_my_performance(ctx_from(request)))


def get_student_performance(request: HttpRequest, student_id: UUID) -> PerformanceOut:
    found = student.get_student_performance(ctx_from(request), student_id=student_id)
    return PerformanceOut.from_view(found)


def get_group_performance(request: HttpRequest, group_id: UUID) -> GroupPerformanceOut:
    found = group.get_group_performance(ctx_from(request), group_id=group_id)
    return GroupPerformanceOut.from_view(found)
