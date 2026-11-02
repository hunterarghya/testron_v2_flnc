from config.email import EmailServer, parse_email_url


def test_mailpit_url() -> None:
    assert parse_email_url("smtp://localhost:1025") == EmailServer(host="localhost", port=1025)


def test_starttls_url_with_credentials() -> None:
    server = parse_email_url("smtp+tls://mailer%40example.com:app%20pass@smtp.example.com:587")

    assert server == EmailServer(
        host="smtp.example.com",
        port=587,
        user="mailer@example.com",
        password="app pass",
        use_tls=True,
    )


def test_ssl_url() -> None:
    server = parse_email_url("smtp+ssl://smtp.example.com:465")

    assert server.use_ssl is True
    assert server.use_tls is False


def test_no_url_means_no_server() -> None:
    assert parse_email_url(None) == EmailServer()
