from django.db import models

from core.clock import now
from core.db.base_model import UUIDModel
from modules.tagging.domain.names import MAX_TAG_NAME_LENGTH, TagKind

_KINDS = [kind.value for kind in TagKind]


class Tag(UUIDModel):
    """A chapter or topic label on questions (database_schema.md §3.3).

    Papers and grades keep tag ids, so a rename shows everywhere at once (ADR-017).
    """

    kind = models.CharField(max_length=8, choices=[(kind, kind) for kind in _KINDS])
    name = models.CharField(max_length=MAX_TAG_NAME_LENGTH)
    normalized_name = models.CharField(max_length=MAX_TAG_NAME_LENGTH)
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "tags"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=models.Q(kind__in=_KINDS), name="tags_kind_valid"),
            models.CheckConstraint(condition=~models.Q(name=""), name="tags_name_not_empty"),
            models.UniqueConstraint(fields=["kind", "normalized_name"], name="tags_kind_name"),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # Prefix suggestions: LIKE 'ce%' can use this index
            models.Index(
                fields=["kind", "normalized_name"],
                opclasses=["text_ops", "text_pattern_ops"],
                name="tags_prefix",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind}: {self.name}"
