from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.results.policies import ensure_teacher


@dataclass(frozen=True, slots=True)
class KeyCorrected:
    version: int
    regraded_attempts: int


def correct_answer_key(
    ctx: Ctx,
    *,
    assignment_id: UUID,
    question_id: UUID,
    entry: assignments.KeyEntry,
    reason: str,
) -> KeyCorrected:
    """D-05 (domain_model.md §6.2, E-14): the key is corrected and every ended attempt is
    regraded, all in one transaction, so published results change at once. Results sits
    above both modules, so it brings the two halves together (ADR-074)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        version = assignments.correct_answer_key_entry(
            ctx, assignment_id=assignment_id, question_id=question_id, entry=entry, reason=reason
        )
        regraded = delivery.regrade_assignment(assignment_id, now=ctx.now)
    return KeyCorrected(version=version, regraded_attempts=regraded)
