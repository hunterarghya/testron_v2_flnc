import json
import logging
import sys

from core.logging import REDACTED, JsonFormatter
from core.request_id import bind_request_id, unbind_request_id


def format_record(message: str = "hello", **extra: object) -> dict[str, object]:
    record = logging.makeLogRecord({"name": "app", "levelname": "INFO", "msg": message, **extra})
    parsed: dict[str, object] = json.loads(JsonFormatter().format(record))
    return parsed


def test_log_line_is_one_json_object() -> None:
    line = format_record("attempt ended")

    assert line["message"] == "attempt ended"
    assert line["level"] == "INFO"
    assert line["logger"] == "app"
    assert str(line["time"]).endswith("+00:00")


def test_log_line_carries_the_current_request_id() -> None:
    token = bind_request_id("req-12345678")
    try:
        line = format_record()
    finally:
        unbind_request_id(token)

    assert line["request_id"] == "req-12345678"


def test_log_line_has_no_request_id_outside_a_request() -> None:
    assert format_record()["request_id"] is None


def test_extra_fields_are_included() -> None:
    assert format_record(attempt_id="a-1")["attempt_id"] == "a-1"


def test_secret_looking_fields_are_redacted() -> None:
    line = format_record(password="hunter2", otp_code="123456", sessionid="abc", status=200)

    assert line["password"] == REDACTED
    assert line["otp_code"] == REDACTED
    assert line["sessionid"] == REDACTED
    assert line["status"] == 200


def test_bengali_text_is_kept_readable() -> None:
    record = logging.makeLogRecord({"msg": "পরীক্ষা"})

    assert "পরীক্ষা" in JsonFormatter().format(record)


def test_exception_trace_is_included() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logging.makeLogRecord({"msg": "failed", "exc_info": sys.exc_info()})

    line = json.loads(JsonFormatter().format(record))

    assert "RuntimeError: boom" in line["exception"]
