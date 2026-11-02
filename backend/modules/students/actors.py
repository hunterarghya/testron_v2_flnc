"""`ACTOR_RESOLVER`: who is making this request, as the area guards need it (ADR-044).

It lives here because an actor is the login (identity) plus the admission status, which
this module owns. One query for a student's status; none for the teacher or a visitor.
"""

from django.http import HttpRequest

from core.context import ANONYMOUS, Actor, Role
from modules.identity.public import session_account
from modules.students.repositories import students


def resolve_actor(request: HttpRequest) -> Actor:
    account = session_account(request)
    if account is None:
        return ANONYMOUS
    user_id, role = account
    status = students.find_status(user_id) if role is Role.STUDENT else None
    return Actor(user_id=user_id, role=role, student_status=status)
