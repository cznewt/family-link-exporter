"""Authentication against Google using an existing logged-in session.

Family Link's web front-end authenticates with the ``SAPISIDHASH`` scheme: it
sends the Google session cookies plus an ``Authorization`` header derived from
the ``SAPISID`` cookie and the current timestamp. We reproduce that here from
cookies harvested by one of three sources:

* a Playwright ``storage_state.json`` (best for headless/servers -- see login.py)
* a Netscape ``cookies.txt`` file
* a locally logged-in browser via ``browser_cookie3`` (desktop only)
"""

from __future__ import annotations

import hashlib
import http.cookiejar
import json
import logging
import time

import httpx

from .config import Family

logger = logging.getLogger(__name__)

# The SAPISID cookie is what the hash is keyed on; fall back to the Secure
# variants some accounts carry instead.
_SAPISID_NAMES = ("SAPISID", "__Secure-3PAPISID", "__Secure-1PAPISID")


class AuthError(RuntimeError):
    """Raised when usable Google credentials cannot be assembled."""


class SapisidHashAuth(httpx.Auth):
    """Adds a fresh ``SAPISIDHASH`` Authorization header to every request."""

    def __init__(self, sapisid: str, origin: str):
        self._sapisid = sapisid
        self._origin = origin

    def auth_flow(self, request):
        request.headers["Authorization"] = self._authorization()
        yield request

    def _authorization(self) -> str:
        ts = int(time.time() * 1000)
        digest = hashlib.sha1(
            f"{ts} {self._sapisid} {self._origin}".encode("utf-8")
        ).hexdigest()
        return f"SAPISIDHASH {ts}_{digest}"


def _sapisid_from_jar(jar: http.cookiejar.CookieJar) -> str | None:
    by_name = {c.name: c.value for c in jar if c.domain.endswith("google.com")}
    for name in _SAPISID_NAMES:
        if by_name.get(name):
            return by_name[name]
    return None


def _load_storage_state(path: str) -> tuple[httpx.Cookies, str | None]:
    """Parse a Playwright ``storage_state.json`` into cookies + SAPISID."""
    with open(path, encoding="utf-8") as fh:
        state = json.load(fh)

    cookies = httpx.Cookies()
    sapisid: str | None = None
    for cookie in state.get("cookies", []):
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        domain = cookie.get("domain", "")
        cookies.set(name, value, domain=domain, path=cookie.get("path", "/"))
        if name in _SAPISID_NAMES and domain.endswith("google.com") and not sapisid:
            sapisid = value
    return cookies, sapisid


def _load_cookie_file(path: str) -> tuple[httpx.Cookies, str | None]:
    """Parse a Netscape ``cookies.txt`` file into cookies + SAPISID."""
    jar = http.cookiejar.MozillaCookieJar(path)
    jar.load(ignore_discard=True, ignore_expires=True)
    return httpx.Cookies(jar), _sapisid_from_jar(jar)


def _load_browser_cookies(browser: str) -> tuple[httpx.Cookies, str | None]:
    try:
        import browser_cookie3
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise AuthError(
            "FLE_COOKIE_BROWSER is set but browser_cookie3 is not installed. "
            "Install the 'localcookies' extra."
        ) from exc

    loader = getattr(browser_cookie3, browser, None)
    if loader is None:
        raise AuthError(f"Unsupported browser {browser!r} for cookie extraction")
    jar = loader(domain_name="google.com")
    return httpx.Cookies(jar), _sapisid_from_jar(jar)


def load_credentials(family: Family) -> tuple[httpx.Cookies, SapisidHashAuth]:
    """Build the cookie jar and auth handler for one family's client."""
    if family.storage_state_path:
        source = f"storage_state {family.storage_state_path}"
        cookies, sapisid = _load_storage_state(family.storage_state_path)
    elif family.cookie_file_path:
        source = f"cookie file {family.cookie_file_path}"
        cookies, sapisid = _load_cookie_file(family.cookie_file_path)
    elif family.cookie_browser:
        source = f"browser {family.cookie_browser}"
        cookies, sapisid = _load_browser_cookies(family.cookie_browser)
    else:  # pragma: no cover - guarded by Family.validate()
        raise AuthError(f"Family {family.name!r}: no credential source configured")

    if not sapisid:
        raise AuthError(
            f"Family {family.name!r}: could not find a SAPISID cookie in {source}. "
            "Make sure the session is logged in to a Google account."
        )

    logger.info("Family %s: loaded Google credentials from %s", family.name, source)
    return cookies, SapisidHashAuth(sapisid, origin="https://familylink.google.com")
