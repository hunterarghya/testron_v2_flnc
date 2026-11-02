"""The only names other modules may import from identity (R-08)."""

from modules.identity.domain.errors import EmailTaken, OtpInvalid, PasswordTooWeak
from modules.identity.domain.values import OtpPurpose
from modules.identity.http_sessions import start_session
from modules.identity.repositories.users import find_user_id_by_email
from modules.identity.services.commands.consume_otp import consume_otp
from modules.identity.services.commands.create_student_user import create_student_user
from modules.identity.services.commands.issue_otp import PRODUCT_NAME, issue_otp
from modules.identity.services.commands.mark_email_verified import mark_email_verified
from modules.identity.services.otp_sending import ensure_can_send_code
from modules.identity.services.password_policy import ensure_password_strong
from modules.identity.services.queries.get_user_summary import UserSummary, get_user_summary

__all__ = [
    "PRODUCT_NAME",
    "EmailTaken",
    "OtpInvalid",
    "OtpPurpose",
    "PasswordTooWeak",
    "UserSummary",
    "consume_otp",
    "create_student_user",
    "ensure_can_send_code",
    "ensure_password_strong",
    "find_user_id_by_email",
    "get_user_summary",
    "issue_otp",
    "mark_email_verified",
    "start_session",
]
