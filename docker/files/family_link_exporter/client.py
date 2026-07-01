"""Read-only client for Google's internal Kids Management API.

This is the same backend the families.google.com web app calls. It is
undocumented and unofficial -- expect it to change. This client only performs
GET requests; the exporter never modifies any Family Link settings.
"""

from __future__ import annotations

import logging

import httpx

from .auth import load_credentials
from .config import Config
from .models import AppUsage, MembersResponse

logger = logging.getLogger(__name__)


class FamilyLinkClient:
    BASE_URL = "https://kidsmanagement-pa.clients6.google.com/kidsmanagement/v1"

    def __init__(self, config: Config):
        self._config = config
        cookies, auth = load_credentials(config)
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            cookies=cookies,
            auth=auth,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) "
                    "Gecko/20100101 Firefox/133.0"
                ),
                "Origin": "https://familylink.google.com",
                "Content-Type": "application/json",
                "X-Goog-Api-Key": config.api_key,
            },
            timeout=30.0,
        )

    def __enter__(self) -> "FamilyLinkClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get_members(self) -> MembersResponse:
        """Return every member of the caller's family."""
        resp = self._client.get("/families/mine/members")
        resp.raise_for_status()
        return MembersResponse.model_validate(resp.json())

    def get_apps_and_usage(self, account_id: str) -> AppUsage:
        """Return installed apps, per-app supervision settings and daily usage."""
        resp = self._client.get(
            f"/people/{account_id}/appsandusage",
            params={
                "capabilities": [
                    "CAPABILITY_APP_USAGE_SESSION",
                    "CAPABILITY_SUPERVISION_CAPABILITIES",
                ]
            },
        )
        resp.raise_for_status()
        return AppUsage.model_validate(resp.json())

    def supervised_account_ids(self) -> list[str]:
        """Auto-discover the user ids of all supervised (child) members."""
        members = self.get_members()
        ids = [m.user_id for m in members.members if m.is_supervised and m.user_id]
        logger.info("Discovered %d supervised member(s)", len(ids))
        return ids
