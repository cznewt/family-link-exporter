"""Runtime configuration, loaded from environment variables (12-factor)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Public web API key used by the families.google.com front-end. Not a secret;
# it only identifies the client project. The actual authorization comes from the
# logged-in Google session cookies (see auth.py).
DEFAULT_API_KEY = "AIzaSyAQb1gupaJhY3CXQy2xmTwJMcjmot3M2hw"

DEFAULT_PORT = 9838
DEFAULT_REFRESH_INTERVAL = 900  # 15 minutes


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Config:
    """All exporter settings. Prefix every env var with ``FLE_``."""

    # --- Authentication (pick exactly one source) ---
    storage_state_path: str | None = None  # FLE_STORAGE_STATE  (Playwright JSON)
    cookie_file_path: str | None = None     # FLE_COOKIE_FILE    (Netscape cookies.txt)
    cookie_browser: str | None = None       # FLE_COOKIE_BROWSER (firefox|chrome|...)

    # --- What to export ---
    # Empty -> auto-discover every supervised member of the family.
    account_ids: list[str] = field(default_factory=list)  # FLE_ACCOUNT_IDS

    # --- HTTP server ---
    host: str = "0.0.0.0"  # FLE_HOST
    port: int = DEFAULT_PORT  # FLE_PORT

    # --- Behaviour ---
    refresh_interval: int = DEFAULT_REFRESH_INTERVAL  # FLE_REFRESH_INTERVAL (seconds)
    timezone: ZoneInfo | None = None  # FLE_TIMEZONE (e.g. Europe/Prague); None -> system local
    api_key: str = DEFAULT_API_KEY  # FLE_API_KEY
    log_level: str = "INFO"  # FLE_LOG_LEVEL

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Config":
        env = env if env is not None else dict(os.environ)

        tz: ZoneInfo | None = None
        tz_name = env.get("FLE_TIMEZONE")
        if tz_name:
            try:
                tz = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError as exc:
                raise ValueError(f"Unknown FLE_TIMEZONE {tz_name!r}") from exc

        return cls(
            storage_state_path=env.get("FLE_STORAGE_STATE"),
            cookie_file_path=env.get("FLE_COOKIE_FILE"),
            cookie_browser=env.get("FLE_COOKIE_BROWSER"),
            account_ids=_split_csv(env.get("FLE_ACCOUNT_IDS")),
            host=env.get("FLE_HOST", "0.0.0.0"),
            port=int(env.get("FLE_PORT", DEFAULT_PORT)),
            refresh_interval=int(env.get("FLE_REFRESH_INTERVAL", DEFAULT_REFRESH_INTERVAL)),
            timezone=tz,
            api_key=env.get("FLE_API_KEY", DEFAULT_API_KEY),
            log_level=env.get("FLE_LOG_LEVEL", "INFO").upper(),
        )

    def has_credential_source(self) -> bool:
        return any(
            [self.storage_state_path, self.cookie_file_path, self.cookie_browser]
        )

    def validate(self) -> None:
        if not self.has_credential_source():
            raise ValueError(
                "No credential source configured. Set one of FLE_STORAGE_STATE, "
                "FLE_COOKIE_FILE or FLE_COOKIE_BROWSER."
            )
