from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.identity.domain.errors import OtpInvalid
from modules.identity.domain.otp import OtpCheck, check_code, hash_code, is_well_formed
from modules.identity.domain.otp import tries_left_after_wrong as tries_left
from modules.identity.domain.values import OtpPurpose
from modules.identity.repositories import email_otps
from modules.identity.services.commands.issue_otp import otp_key


def consume_otp(ctx: Ctx, *, user_id: UUID, purpose: OtpPurpose, code: str) -> None:
    """Use up the live code if `code` matches it (domain_model.md §3.1 #2, #3; V1 F-01).

    A missing, malformed, expired, used or locked code is refused with one message.
    A wrong code counts a try; after 5 the code is dead. The try must be saved even
    though OtpInvalid is raised, so this commits on its own and refuses to run inside
    another transaction (`durable=True`).
    """
    if not is_well_formed(code):
        raise OtpInvalid()
    submitted = hash_code(code, key=otp_key())
    wrong_try_context: dict[str, object] | None = None
    with transaction.atomic(durable=True):
        found = email_otps.get_live_otp_for_update(user_id, purpose)
        outcome = check_code(found[1] if found else None, submitted_hash=submitted, now=ctx.now)
        if found and outcome is OtpCheck.ACCEPTED:
            email_otps.consume_otp(found[0], now=ctx.now)
            return
        if found and outcome is OtpCheck.WRONG:
            email_otps.record_failed_try(found[0])
            wrong_try_context = {"tries_left": tries_left(found[1])}
    # Raised only after the block, so the counted try is already committed
    raise OtpInvalid(context=wrong_try_context)
