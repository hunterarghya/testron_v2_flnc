"""The frozen paper and its answer key (database_schema.md §3.5, §4.2-4.3).

The paper holds no answers by construction; a database trigger refuses any change to it
(migration 0002). Only the answer key changes, through audited corrections."""

from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import Range

from core.clock import now
from core.db.base_model import UUIDModel
from modules.assignments.models.assignment import Assignment


class Paper(models.Model):
    assignment = models.OneToOneField(
        Assignment, primary_key=True, on_delete=models.RESTRICT, related_name="paper"
    )
    content = models.JSONField()
    # SHA-256 of the canonical JSON: two assignments of an unchanged test share it
    content_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "papers"

    def __str__(self) -> str:
        return f"paper {self.assignment_id}"


class AnswerKey(models.Model):
    assignment = models.OneToOneField(
        Assignment, primary_key=True, on_delete=models.RESTRICT, related_name="answer_key"
    )
    version = models.IntegerField(default=1)
    entries = models.JSONField()
    solutions = models.JSONField()
    updated_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "answer_keys"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=Q(version__gte=1), name="answer_keys_version_min"),
        ]

    def __str__(self) -> str:
        return f"key {self.assignment_id} v{self.version}"


class AnswerKeyCorrection(UUIDModel):
    answer_key = models.ForeignKey(
        AnswerKey, on_delete=models.RESTRICT, related_name="corrections", db_column="assignment_id"
    )
    question_id = models.UUIDField()
    before = models.JSONField()
    after = models.JSONField()
    reason = models.TextField()
    version_after = models.IntegerField()
    corrected_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "answer_key_corrections"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=Range(Length("reason"), (1, 500)),
                name="answer_key_corrections_reason_length",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["answer_key", "corrected_at"], name="answer_key_corrections_when"),
        ]

    def __str__(self) -> str:
        return f"correction {self.question_id}"
