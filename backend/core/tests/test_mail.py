from smtplib import SMTPException

import pytest
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from pytest_django.fixtures import Settings as DjangoSettings

from core.mail import send

CONTEXT = {
    "name": "Rina & Co",
    "code": "482913",
    "expires_in_minutes": 10,
}


def brand_name() -> str:
    return "Bio Classes"


@pytest.fixture(autouse=True)
def branding(settings: DjangoSettings) -> None:
    # The real hook reads the database; these tests don't need one
    settings.MAIL_BRAND_NAME = "core.tests.test_mail.brand_name"


def test_mail_is_sent_with_text_and_html() -> None:
    assert send("identity/email/verify_email", to="rina@example.com", context=CONTEXT)

    message = mail.outbox[0]
    assert isinstance(message, EmailMultiAlternatives)
    assert message.to == ["rina@example.com"]
    assert message.subject == "482913 is your Bio Classes verification code"
    assert "482913" in str(message.body)
    assert message.alternatives[0][1] == "text/html"


def test_text_part_is_not_html_escaped() -> None:
    send("identity/email/verify_email", to="rina@example.com", context=CONTEXT)

    assert "Hello Rina & Co," in str(mail.outbox[0].body)


def test_html_part_escapes_names() -> None:
    send(
        "identity/email/verify_email", to="x@example.com", context=CONTEXT | {"name": "<b>Rina</b>"}
    )

    message = mail.outbox[0]
    assert isinstance(message, EmailMultiAlternatives)
    html = str(message.alternatives[0][0])
    assert "&lt;b&gt;Rina&lt;/b&gt;" in html


def test_reset_template_exists() -> None:
    assert send("identity/email/reset_password", to="rina@example.com", context=CONTEXT)
    assert "password reset code" in mail.outbox[0].subject


def test_failure_is_logged_not_raised(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def refuse(self: EmailMultiAlternatives) -> int:
        raise SMTPException("mail server said no")

    monkeypatch.setattr(EmailMultiAlternatives, "send", refuse)

    assert send("identity/email/verify_email", to="rina@example.com", context=CONTEXT) is False
    assert "mail.send failed" in caplog.text
    assert "482913" not in caplog.text
