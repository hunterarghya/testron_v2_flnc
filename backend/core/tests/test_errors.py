from core.errors import AccountNotActive, Conflict, DomainError, Forbidden, NotFound


class StageClosed(Conflict):
    code = "stage_closed"
    title = "This section has closed"


def test_subclass_declares_code_status_and_title_once() -> None:
    error = StageClosed(context={"stage_index": 1})

    assert (error.code, error.status, error.title) == ("stage_closed", 409, "This section has closed")
    assert error.context == {"stage_index": 1}


def test_message_falls_back_to_the_title() -> None:
    assert str(Forbidden()) == "You can't do this"
    assert Forbidden().detail is None


def test_not_found_names_the_resource_but_nothing_more() -> None:
    error = NotFound("attempt")

    assert (error.code, error.status) == ("not_found", 404)
    assert error.detail == "The attempt was not found."


def test_every_core_error_is_a_domain_error() -> None:
    assert issubclass(AccountNotActive, DomainError)
    assert AccountNotActive.status == 403
