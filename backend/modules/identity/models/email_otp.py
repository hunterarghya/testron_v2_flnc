from django.db import models

from core.clock import now
from core.db.base_model import UUIDModel
from modules.identity.domain.values import MAX_OTP_FAILED_TRIES, OtpPurpose
from modules.identity.models.user import User


class EmailOtp(UUIDModel):
    """A one-time code sent by email, stored only as a hash (domain_model.md §3.1)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    purpose = models.CharField(max_length=16, choices=[(p.value, p.value) for p in OtpPurpose])
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    failed_tries = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True)
    # Set when a newer code for the same purpose is issued
    superseded_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "email_otps"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=models.Q(purpose__in=[p.value for p in OtpPurpose]),
                name="email_otps_purpose_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(failed_tries__lte=MAX_OTP_FAILED_TRIES),
                name="email_otps_failed_tries_max",
            ),
            # At most one live code per (user, purpose) (domain_model.md §3.1 #1)
            models.UniqueConstraint(
                fields=["user", "purpose"],
                condition=models.Q(consumed_at__isnull=True, superseded_at__isnull=True),
                name="email_otps_one_live",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # The resend cooldown and the per-hour count
            models.Index(
                "user", "purpose", models.F("created_at").desc(), name="email_otps_recent"
            ),
        ]
