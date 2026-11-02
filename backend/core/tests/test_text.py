import pytest

from core.text import clean_text_line

ZWNJ, ZWJ = chr(0x200C), chr(0x200D)
RIGHT_TO_LEFT_OVERRIDE = chr(0x202E)


@pytest.mark.parametrize(
    ("raw", "clean"),
    [
        ("Rina Das", "Rina Das"),
        ("  Rina   Das  ", "Rina Das"),
        ("Rina\tDas\n", "Rina Das"),
        ("Rina\x00\x07 Das", "Rina Das"),
        (f"Rina{RIGHT_TO_LEFT_OVERRIDE}saD", "RinasaD"),
        ("রিনা দাস", "রিনা দাস"),
        (f"র{ZWJ}্য", f"র{ZWJ}্য"),
        (f"ক্{ZWNJ}ষ", f"ক্{ZWNJ}ষ"),
        ("é", "é"),
        (" \t ", ""),
    ],
    ids=[
        "plain",
        "extra-spaces",
        "tabs-and-newlines",
        "control-characters",
        "bidi-override-removed",
        "bengali",
        "bengali-joiner-kept",
        "bengali-non-joiner-kept",
        "combined-accent-normalized",
        "only-whitespace",
    ],
)
def test_clean_text_line(raw: str, clean: str) -> None:
    assert clean_text_line(raw) == clean
