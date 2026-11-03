from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Q

from modules.grading.domain.marking import Outcome

_OUTCOMES = [outcome.value for outcome in Outcome]


class Grade(models.Model):
    """One question's marks in one ended attempt (domain_model.md §3.7). Every ended attempt
    has one per paper question, unanswered ones included."""

    pk = models.CompositePrimaryKey("attempt_id", "question_id")
    # Named, not imported: delivery's models stay private to it
    attempt = models.ForeignKey("delivery.Attempt", on_delete=models.CASCADE, related_name="+")
    # A paper question id
    question_id = models.UUIDField()
    section_index = models.SmallIntegerField()
    outcome = models.CharField(max_length=16, choices=[(o, o) for o in _OUTCOMES])
    marks_awarded = models.DecimalField(max_digits=7, decimal_places=2)
    max_marks = models.DecimalField(max_digits=7, decimal_places=2)
    # Copied from the paper so performance reports group by tag cheaply (database_schema.md §3.7)
    tag_ids = ArrayField(models.UUIDField(), default=list)

    class Meta:
        db_table = "grades"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=Q(outcome__in=_OUTCOMES), name="grades_outcome_valid"),
            models.CheckConstraint(condition=Q(max_marks__gt=0), name="grades_max_marks_positive"),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            GinIndex(fields=["tag_ids"], name="grades_tag_ids"),
        ]

    def __str__(self) -> str:
        return f"{self.question_id} in {self.attempt_id}: {self.marks_awarded}"
