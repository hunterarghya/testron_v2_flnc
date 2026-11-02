"""Send one email, inline, with a short timeout (architecture.md §5.10).

There is no worker, so mail is sent inside the request. A failure is logged at ERROR
(with the request id) and reported as False, never raised: sign-up and password reset
must answer the same whether or not the email went out, and the user can press Resend.

A template name `x/y` means three files: `x/y.subject.txt`, `x/y.txt` and `x/y.html`.
Every template gets `coaching_name`. Core can't import the module that stores it, so the
function that reads it is named by the `MAIL_BRAND_NAME` setting (a dotted path, ADR-060).
"""

import logging
from collections.abc import Callable, Mapping
from functools import cache
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


def send(template: str, *, to: str, context: Mapping[str, object]) -> bool:
    """Render and send `template` to one address. True when the mail server accepted it."""
    branded = {"coaching_name": _brand_name(), **context}
    message = _render(template, to=to, context=branded)
    try:
        message.send()
    except (SMTPException, OSError):
        # The address and the context (which may hold a code) stay out of the log
        logger.exception("mail.send failed", extra={"template": template})
        return False
    return True


def _render(template: str, *, to: str, context: dict[str, object]) -> EmailMultiAlternatives:
    subject = render_to_string(f"{template}.subject.txt", context).strip()
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f"{template}.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    message.attach_alternative(render_to_string(f"{template}.html", context), "text/html")
    return message


def _brand_name() -> str:
    return _brand_reader(settings.MAIL_BRAND_NAME)()


@cache
def _brand_reader(path: str) -> Callable[[], str]:
    reader: Callable[[], str] = import_string(path)
    return reader
