"""A test's content: sections, questions, options and question tags (database_schema.md §3.4).

Positions are unique per parent but checked at commit time (DEFERRABLE INITIALLY DEFERRED),
so a reorder can swap positions inside one transaction.
"""

from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual

from core.db.base_model import TimestampedModel, UUIDModel
from modules.authoring.domain.section_rules import MAX_SECTION_TITLE_LENGTH
from modules.authoring.domain.values import QuestionType
from modules.authoring.models.test import Test

_TYPES = [kind.value for kind in QuestionType]


def _position_unique(parent: str, name: str) -> models.UniqueConstraint:
    return models.UniqueConstraint(
        fields=[parent, "position"], name=name, deferrable=models.Deferrable.DEFERRED
    )


class Section(UUIDModel):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="sections")
    position = models.PositiveSmallIntegerField()
    title = models.TextField(default="", blank=True)
    instructions = models.JSONField(null=True)
    # Required only for SECTIONED tests; a missing one is a validation problem, not an error
    duration_s = models.IntegerField(null=True)

    class Meta:
        db_table = "sections"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            _position_unique("test", "sections_test_position"),
            models.CheckConstraint(
                condition=LessThanOrEqual(Length("title"), MAX_SECTION_TITLE_LENGTH),
                name="sections_title_length",
            ),
            models.CheckConstraint(
                condition=Q(duration_s__isnull=True) | Q(duration_s__gte=60),
                name="sections_duration_min",
            ),
        ]

    def __str__(self) -> str:
        return self.title or f"Section {self.position + 1}"


class Question(TimestampedModel):
    # Copied from the section, for "every question of a test" (kept in step by the service)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="+")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="questions")
    position = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=16, choices=[(kind, kind) for kind in _TYPES])
    stem = models.JSONField()
    solution = models.JSONField(null=True)
    marks_override = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    negative_marks_override = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    time_override_s = models.IntegerField(null=True)
    numeric_answer = models.DecimalField(max_digits=20, decimal_places=6, null=True)
    numeric_tolerance = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    search_text = models.TextField(default="", blank=True)
    tags = models.ManyToManyField("tagging.Tag", through="QuestionTag", related_name="+")

    class Meta:
        db_table = "questions"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            _position_unique("section", "questions_section_position"),
            models.CheckConstraint(condition=Q(type__in=_TYPES), name="questions_type_valid"),
            models.CheckConstraint(
                condition=Q(marks_override__isnull=True) | Q(marks_override__gt=0),
                name="questions_marks_override_positive",
            ),
            models.CheckConstraint(
                condition=Q(negative_marks_override__isnull=True)
                | Q(negative_marks_override__gte=0),
                name="questions_negative_override_not_negative",
            ),
            models.CheckConstraint(
                condition=Q(time_override_s__isnull=True) | Q(time_override_s__gte=5),
                name="questions_time_override_min",
            ),
            models.CheckConstraint(
                condition=Q(numeric_tolerance__gte=0), name="questions_tolerance_not_negative"
            ),
            # Only numerical questions have an answer value or a tolerance
            models.CheckConstraint(
                condition=Q(type="NUMERICAL") | Q(numeric_answer__isnull=True, numeric_tolerance=0),
                name="questions_numeric_fields",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["test"], name="questions_test"),
        ]

    def __str__(self) -> str:
        return self.search_text[:60]


class Option(UUIDModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    position = models.PositiveSmallIntegerField()
    content = models.JSONField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "options"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            _position_unique("question", "options_question_position"),
        ]

    def __str__(self) -> str:
        return f"{self.question_id}:{self.position}"


class QuestionTag(models.Model):
    pk = models.CompositePrimaryKey("question_id", "tag_id")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    # Named, not imported: tagging's models stay private to it. Deleting a tag removes it here.
    tag = models.ForeignKey("tagging.Tag", on_delete=models.CASCADE, related_name="+")

    class Meta:
        db_table = "question_tags"
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # Tag usage counts and the library's tag filter
            models.Index(fields=["tag"], name="question_tags_tag"),
        ]

    def __str__(self) -> str:
        return f"{self.question_id}:{self.tag_id}"
