"""Interactive helper that captures a reusable Google session.

Run once on a machine with a display (or with ``xvfb``/VNC) to log in -- 2FA
included -- and persist the cookies to a ``storage_state.json`` the exporter can
then load headlessly. Refresh it when the session eventually expires.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

FAMILY_LINK_URL = "https://familylink.google.com"


def interactive_login(
    storage_state_path: str, headless: bool = False, channel: str | None = None
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "Playwright is not installed. Install the 'login' extra:\n"
            "    pip install 'family-link-exporter[login]'\n"
            "    playwright install chromium"
        ) from exc

    # Google blocks sign-in in obviously-automated browsers ("This browser or app
    # may not be secure"). Driving a real installed browser (channel="chrome" or
    # "msedge") and dropping the automation flags gets past it more often; bundled
    # Chromium is the most likely to be blocked.
    launch_kwargs = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
        "ignore_default_args": ["--enable-automation"],
    }
    if channel:
        launch_kwargs["channel"] = channel

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kwargs)
        context = browser.new_context()
        page = context.new_page()
        page.goto(FAMILY_LINK_URL)

        print(
            "\nA browser window has opened. Log in to the *parent* Google account,\n"
            "complete any 2FA, and wait until you can see the Family Link dashboard.\n"
            "If Google says 'this browser may not be secure', close it and retry with\n"
            "  --channel chrome   (run `playwright install chrome` first), or use the\n"
            "cookie-export method in the README.\n"
        )
        input("Press Enter here once you are logged in to save the session... ")

        context.storage_state(path=storage_state_path)
        browser.close()

    logger.info("Saved Google session to %s", storage_state_path)
    print(f"\nSaved session to {storage_state_path}. Point FLE_STORAGE_STATE at it.")
