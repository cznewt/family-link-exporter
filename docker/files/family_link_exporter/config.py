"""Runtime configuration, loaded from environment variables (12-factor).

Single family (default): credentials come from FLE_STORAGE_STATE / FLE_COOKIE_FILE
/ FLE_COOKIE_BROWSER, labelled with FLE_FAMILY_NAME (default "default").

Multiple families: point FLE_CONFIG at a YAML file:

    families:
      - name: smith
        cookieFile: /etc/family-link/families/smith/cookies.txt
      - name: jones
        storageState: /etc/family-link/families/jones/storage_state.json
        accountIds: ["123"]      # optional; default = all supervised kids
"""

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
class Family:
    """One supervised family = one parent Google account + its credential."""

    name: str
    storage_state_path: str | None = None
    cookie_file_path: str | None = None
    cookie_browser: str | None = None
    # Empty -> auto-discover every supervised member of this family.
    account_ids: list[str] = field(default_factory=list)

    def has_credential_source(self) -> bool:
        return any(
            [self.storage_state_path, self.cookie_file_path, self.cookie_browser]
        )

    def validate(self) -> None:
        if not self.has_credential_source():
            raise ValueError(
                f"Family {self.name!r}: no credential source "
                "(need one of storageState / cookieFile / cookieBrowser)."
            )


def _load_families(path: str) -> list[Family]:
    import yaml  # pyyaml; only needed in multi-family mode

    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    families: list[Family] = []
    for i, item in enumerate(data.get("families", [])):
        families.append(
            Family(
                name=str(item.get("name") or f"family-{i}"),
                storage_state_path=item.get("storageState"),
                cookie_file_path=item.get("cookieFile"),
                cookie_browser=item.get("cookieBrowser"),
                account_ids=[str(a) for a in (item.get("accountIds") or [])],
            )
        )
    if not families:
        raise ValueError(f"FLE_CONFIG {path!r} defines no families")
    return families


@dataclass
class Config:
    """All exporter settings. Prefix every env var with ``FLE_``."""

    families: list[Family] = field(default_factory=list)

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

        config_path = env.get("FLE_CONFIG")
        if config_path:
            families = _load_families(config_path)
        else:
            families = [
                Family(
                    name=env.get("FLE_FAMILY_NAME", "default"),
                    storage_state_path=env.get("FLE_STORAGE_STATE"),
                    cookie_file_path=env.get("FLE_COOKIE_FILE"),
                    cookie_browser=env.get("FLE_COOKIE_BROWSER"),
                    account_ids=_split_csv(env.get("FLE_ACCOUNT_IDS")),
                )
            ]

        return cls(
            families=families,
            host=env.get("FLE_HOST", "0.0.0.0"),
            port=int(env.get("FLE_PORT", DEFAULT_PORT)),
            refresh_interval=int(env.get("FLE_REFRESH_INTERVAL", DEFAULT_REFRESH_INTERVAL)),
            timezone=tz,
            api_key=env.get("FLE_API_KEY", DEFAULT_API_KEY),
            log_level=env.get("FLE_LOG_LEVEL", "INFO").upper(),
        )

    def has_credential_source(self) -> bool:
        return any(f.has_credential_source() for f in self.families)
