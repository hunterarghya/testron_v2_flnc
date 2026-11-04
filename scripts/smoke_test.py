"""Check a running deployment end to end (docs/hosting_guide.md "Smoke test", ADR-086).

Health (database included), the SPA shell with its security headers, HTTP to HTTPS, a guarded
teacher page refusing a stranger, and a real teacher login reaching the dashboard. Prints one
line per check and exits 1 if any fails. Uses only the standard library.

Usage: python scripts/smoke_test.py https://tests.example.com --email teacher@example.com
       (asks for the password, or reads SMOKE_TEST_PASSWORD; --insecure accepts a local
       self-signed certificate)
"""

import argparse
import getpass
import http.cookiejar
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from email.message import Message
from typing import Any

OK = 200
REDIRECTS = (301, 302, 307, 308)
REFUSED = (401, 403)
Answer = tuple[int, Message, bytes]


class CheckFailed(Exception):
    pass


def expect(condition: bool, problem: str) -> None:
    if not condition:
        raise CheckFailed(problem)


class Site:
    def __init__(self, base: str, *, insecure: bool) -> None:
        expect(base.startswith(("https://", "http://")), f"not a web address: {base}")
        self.base = base.rstrip("/")
        context = ssl.create_default_context()
        if insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=context),
            urllib.request.HTTPCookieProcessor(self.cookies),
            _NoRedirects(),
        )

    def send(self, method: str, path: str, body: dict[str, str] | None = None) -> Answer:
        # Django checks the origin of every secure unsafe request (CSRF)
        headers = {"Origin": self.base, "Referer": self.base + "/", "Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers |= {"Content-Type": "application/json", "X-CSRFToken": self.cookie("csrftoken")}
        # The scheme was checked in __init__ (ADR-086): only http(s) addresses get here
        url = self.base + path
        request = urllib.request.Request(url, data=data, headers=headers, method=method)  # noqa: S310
        try:
            with self.opener.open(request, timeout=30) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.headers, error.read()

    def cookie(self, name: str) -> str:
        return next((c.value or "" for c in self.cookies if c.name == name), "")


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def checks(site: Site, email: str, password: str) -> list[tuple[str, Callable[[], str]]]:
    def health() -> str:
        status, _, body = site.send("GET", "/api/v1/healthz?deep=1")
        expect(status == OK, f"status {status}: {body[:200]!r}")
        found = json.loads(body)
        return f"version {found['version']} ({found['commit'][:7]})"

    def shell() -> str:
        status, headers, body = site.send("GET", "/")
        expect(status == OK, f"status {status}")
        expect(b"<html" in body.lower(), "the page isn't the app")
        wanted = ("Strict-Transport-Security", "Content-Security-Policy")
        missing = [name for name in wanted if not headers.get(name)]
        expect(not missing, f"missing headers: {', '.join(missing)}")
        return "HSTS and CSP present"

    def http_redirects() -> str:
        plain = Site(site.base.replace("https://", "http://", 1), insecure=True)
        status, headers, _ = plain.send("GET", "/")
        location = headers.get("Location", "")
        expect(status in REDIRECTS, f"status {status}")
        expect(location.startswith("https://"), f"goes to {location!r}")
        return f"{status} to {location}"

    def stranger_refused() -> str:
        status, _, _ = Site(site.base, insecure=True).send("GET", "/api/v1/admin/dashboard")
        expect(status in REFUSED, f"status {status}")
        return f"{status} without a login"

    def teacher_login() -> str:
        site.send("GET", "/api/v1/auth/csrf")
        credentials = {"email": email, "password": password}
        status, _, body = site.send("POST", "/api/v1/auth/login", credentials)
        expect(status == OK, f"login status {status}: {body[:200]!r}")
        status, _, _ = site.send("GET", "/api/v1/admin/dashboard")
        expect(status == OK, f"dashboard status {status}")
        return "logged in and opened the dashboard"

    return [
        ("Health (with the database)", health),
        ("The app page and its security headers", shell),
        ("HTTP goes to HTTPS", http_redirects),
        ("Teacher pages refuse a stranger", stranger_refused),
        ("The teacher can log in", teacher_login),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("base_url")
    parser.add_argument("--email", required=True, help="The teacher's email")
    parser.add_argument("--insecure", action="store_true", help="Accept a self-signed certificate")
    args = parser.parse_args()
    password = os.environ.get("SMOKE_TEST_PASSWORD") or getpass.getpass("Teacher's password: ")
    site = Site(args.base_url, insecure=args.insecure)
    failed = 0
    for name, check in checks(site, args.email, password):
        try:
            sys.stdout.write(f"PASS  {name}: {check()}\n")
        except (CheckFailed, OSError, ValueError, KeyError) as problem:
            failed += 1
            sys.stdout.write(f"FAIL  {name}: {problem}\n")
    sys.stdout.write("All checks passed.\n" if not failed else f"{failed} check(s) failed.\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
