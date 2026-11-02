from config.database import database_settings

NEON_POOLED = (
    "postgresql://app:p%40ss@ep-cool-1234-pooler.ap-southeast-1.aws.neon.tech/app"
    "?sslmode=require&channel_binding=require"
)
NEON_DIRECT = "postgresql://app:p%40ss@ep-cool-1234.ap-southeast-1.aws.neon.tech/app"


def test_url_parts_are_mapped() -> None:
    default = database_settings("postgres://app:secret@localhost:5432/app", direct_url=None)[
        "default"
    ]

    assert default["NAME"] == "app"
    assert default["USER"] == "app"
    assert default["PASSWORD"] == "secret"
    assert default["HOST"] == "localhost"
    assert default["PORT"] == "5432"


def test_encoded_password_is_decoded() -> None:
    assert database_settings(NEON_POOLED, direct_url=None)["default"]["PASSWORD"] == "p@ss"


def test_pooler_safe_options_are_set() -> None:
    default = database_settings(NEON_POOLED, direct_url=None)["default"]

    assert default["CONN_MAX_AGE"] == 0
    assert default["DISABLE_SERVER_SIDE_CURSORS"] is True
    assert default["ATOMIC_REQUESTS"] is False
    assert default["OPTIONS"] == {
        "prepare_threshold": None,
        "sslmode": "require",
        "channel_binding": "require",
    }


def test_direct_alias_uses_the_direct_url() -> None:
    databases = database_settings(NEON_POOLED, direct_url=NEON_DIRECT)

    assert databases["default"]["HOST"] == "ep-cool-1234-pooler.ap-southeast-1.aws.neon.tech"
    assert databases["direct"]["HOST"] == "ep-cool-1234.ap-southeast-1.aws.neon.tech"


def test_direct_alias_falls_back_to_the_main_url() -> None:
    databases = database_settings("postgres://app:app@localhost:5432/app", direct_url=None)

    assert databases["direct"]["HOST"] == "localhost"
    assert databases["direct"]["TEST"] == {"MIRROR": "default"}
