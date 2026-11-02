import base64
import hashlib
from pathlib import Path

from core.http.csp import content_security_policy, inline_script_hashes, spa_script_hashes


def sha(script: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(script.encode()).digest()).decode() + "'"


def test_only_inline_code_scripts_are_hashed() -> None:
    html = (
        '<script type="importmap">{"imports":{}}</script>'
        '<script type="module" src="/a.js"></script>'
        '<script type="application/json" id="data">[1]</script>'
        "<script>window.x=1;</script>"
        "<script>   </script>"
    )

    assert inline_script_hashes(html) == [sha('{"imports":{}}'), sha("window.x=1;")]


def test_hashes_are_collected_from_every_page(tmp_path: Path) -> None:
    (tmp_path / "admin").mkdir()
    (tmp_path / "index.html").write_text("<script>a()</script>", encoding="utf-8")
    (tmp_path / "admin" / "index.html").write_text(
        "<script>a()</script><script>b()</script>", encoding="utf-8"
    )

    assert spa_script_hashes(str(tmp_path)) == tuple(sorted({sha("a()"), sha("b()")}))


def test_without_a_build_scripts_are_self_only() -> None:
    assert "script-src 'self';" in content_security_policy(None)
