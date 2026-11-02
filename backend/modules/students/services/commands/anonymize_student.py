from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import NotFound
from modules.identity import public as identity
from modules.students.domain.admission import AdmissionAction, can_apply
from modules.students.domain.anonymization import (
    anonymized_email,
    anonymized_name,
    ensure_name_confirmed,
)
from modules.students.domain.errors import AdmissionStepNotAllowed
from modules.students.policies import ensure_teacher
from modules.students.repositories import students


def anonymize_student(ctx: Ctx, *, student_id: UUID, confirm_name: str) -> None:
    """Delete a student permanently: "Deleted student #n" (domain_model.md §3.2 #3, T-14).

    The teacher types the student's exact name first (security.md T-08). The name, email,
    password, Google link, sessions and performance sharing go; attempts, responses and
    grades stay, so gradebooks and statistics remain intact. Only ACTIVE or DEACTIVATED
    students can be deleted. It can't be undone.
    """
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        status = students.lock_statuses_for_update([student_id]).get(student_id)
        if status is None:
            raise NotFound("student")
        if not can_apply(AdmissionAction.ANONYMIZE, status):
            raise AdmissionStepNotAllowed(context={"status": status})
        ensure_name_confirmed(confirm_name, name=identity.get_user_summary(student_id).name)
        number = students.next_anonymized_number()
        identity.scrub_account(
            ctx, user_id=student_id, name=anonymized_name(number), email=anonymized_email(number)
        )
        students.mark_anonymized(student_id, number=number, now=ctx.now)
