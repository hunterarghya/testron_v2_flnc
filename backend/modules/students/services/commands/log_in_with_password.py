from core.context import Ctx
from modules.identity import public as identity
from modules.students.services.session_user import SessionUserView, build_session_user


def log_in_with_password(ctx: Ctx, *, email: str, password: str, client_ip: str) -> SessionUserView:
    """Log in with email and password (domain_model.md §3.1 #3, S-01).

    Identity checks the credentials (one generic error, rate limits). Pending, declined
    and deactivated students may log in: the SPA shows them their status screen. The
    controller then starts the session.
    """
    user_id = identity.authenticate_password(
        ctx, email=email, password=password, client_ip=client_ip
    )
    return build_session_user(user_id)
