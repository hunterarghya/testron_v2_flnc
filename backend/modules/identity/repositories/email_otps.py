from datetime import datetime
from uuid import UUID

from django.db.models import F, QuerySet

from core.db.locking import for_update
from modules.identity.domain.otp import LiveOtp
from modules.identity.domain.values import OtpPurpose
from modules.identity.models import EmailOtp


def get_live_otp_for_update(user_id: UUID, purpose: OtpPurpose) -> tuple[UUID, LiveOtp] | None:
    """The one live code for (user, purpose) with its id, locked; None when there is none."""
    live = EmailOtp.objects.filter(
        user_id=user_id, purpose=purpose, consumed_at__isnull=True, superseded_at__isnull=True
    )
    otp = for_update(live).first()
    if otp is None:
        return None
    return otp.id, LiveOtp(
        code_hash=otp.code_hash, expires_at=otp.expires_at, failed_tries=otp.failed_tries
    )


def supersede_live_otps(user_id: UUID, purpose: OtpPurpose, *, now: datetime) -> None:
    EmailOtp.objects.filter(
        user_id=user_id, purpose=purpose, consumed_at__isnull=True, superseded_at__isnull=True
    ).update(superseded_at=now)


def insert_otp(
    user_id: UUID, purpose: OtpPurpose, *, code_hash: str, expires_at: datetime, now: datetime
) -> None:
    EmailOtp.objects.create(
        user_id=user_id,
        purpose=purpose,
        code_hash=code_hash,
        expires_at=expires_at,
        created_at=now,
    )


def record_failed_try(otp_id: UUID) -> None:
    EmailOtp.objects.filter(pk=otp_id).update(failed_tries=F("failed_tries") + 1)


def consume_otp(otp_id: UUID, *, now: datetime) -> None:
    EmailOtp.objects.filter(pk=otp_id).update(consumed_at=now)


def created_before(instant: datetime) -> QuerySet[EmailOtp]:
    return EmailOtp.objects.filter(created_at__lt=instant)
