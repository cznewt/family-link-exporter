"""Turn raw API responses into a normalized, metrics-friendly snapshot.

Kept separate from the Prometheus wiring so it can be unit-tested and reused
(e.g. by the ``dump`` command) without a running HTTP server.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime

from .client import FamilyLinkClient
from .config import Config
from .models import AppUsage, MembersResponse

logger = logging.getLogger(__name__)


@dataclass
class AppSnapshot:
    package: str
    title: str
    usage_seconds: float = 0.0
    daily_limit_minutes: int | None = None
    limit_enabled: bool = False
    blocked: bool = False
    always_allowed: bool = False


@dataclass
class DeviceSnapshot:
    device_id: str
    model: str
    friendly_name: str
    last_activity_seconds: float | None = None


@dataclass
class ChildSnapshot:
    account_id: str
    name: str
    apps: list[AppSnapshot] = field(default_factory=list)
    devices: list[DeviceSnapshot] = field(default_factory=list)

    @property
    def total_usage_seconds(self) -> float:
        return sum(app.usage_seconds for app in self.apps)


@dataclass
class Snapshot:
    children: list[ChildSnapshot] = field(default_factory=list)
    success: bool = False
    duration_seconds: float = 0.0
    timestamp: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 3),
            "error": self.error,
            "children": [
                {
                    "account_id": c.account_id,
                    "name": c.name,
                    "total_usage_seconds": round(c.total_usage_seconds, 1),
                    "apps": [vars(a) for a in c.apps],
                    "devices": [vars(d) for d in c.devices],
                }
                for c in self.children
            ],
        }


def _millis_to_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return int(value) / 1000.0
    except (ValueError, TypeError):
        return None


def build_child_snapshot(
    account_id: str,
    name: str,
    data: AppUsage,
    today: tuple[int, int, int],
) -> ChildSnapshot:
    """Normalize one child's appsandusage response.

    ``today`` is a (year, month, day) tuple in the family's timezone; only usage
    sessions dated today are summed into the live "today so far" figure.
    """
    # Settings + metadata come from the apps list, keyed by package name.
    apps: dict[str, AppSnapshot] = {}
    for app in data.apps:
        setting = app.supervision_setting
        limit = setting.usage_limit
        apps[app.package_name] = AppSnapshot(
            package=app.package_name,
            title=app.title or app.package_name,
            daily_limit_minutes=limit.daily_usage_limit_mins if limit else None,
            limit_enabled=bool(limit and limit.enabled),
            blocked=setting.hidden,
            always_allowed=setting.always_allowed,
        )

    # Usage is summed across devices for the current day.
    for session in data.app_usage_sessions:
        if (session.date.year, session.date.month, session.date.day) != today:
            continue
        package = session.app_id.android_app_package_name
        if not package:
            continue
        snap = apps.get(package)
        if snap is None:
            # Usage for an app no longer in the installed list -> keep it anyway.
            snap = AppSnapshot(package=package, title=package)
            apps[package] = snap
        snap.usage_seconds += session.usage_seconds()

    devices = [
        DeviceSnapshot(
            device_id=dev.device_id,
            model=dev.display_info.model,
            friendly_name=dev.display_info.friendly_name,
            last_activity_seconds=_millis_to_seconds(
                dev.display_info.last_activity_time_millis
            ),
        )
        for dev in data.device_info
    ]

    return ChildSnapshot(
        account_id=account_id,
        name=name,
        apps=list(apps.values()),
        devices=devices,
    )


def _resolve_targets(
    config: Config, client: FamilyLinkClient
) -> tuple[list[str], dict[str, str]]:
    """Return (account_ids, id -> display name). Names best-effort."""
    names: dict[str, str] = {}
    members: MembersResponse | None = None
    try:
        members = client.get_members()
        for member in members.members:
            names[member.user_id] = member.label
    except Exception:  # noqa: BLE001 - names are optional, keep going
        logger.warning("Could not fetch member names", exc_info=True)

    # Explicit allow-list wins.
    if config.account_ids:
        return config.account_ids, names

    # Otherwise export every supervised child we can see.
    if members is not None:
        supervised = [
            m.user_id for m in members.members if m.is_supervised and m.user_id
        ]
        if supervised:
            return supervised, names

    # Last resort: a dedicated discovery call (may raise -> unhealthy scrape).
    return client.supervised_account_ids(), names


def collect_snapshot(config: Config) -> Snapshot:
    """Fetch everything once and return a normalized snapshot.

    Builds its own client from ``config`` so a rotated session file is picked up
    each call, and any credential/API problem (including no credentials at all)
    is caught and surfaced as an unhealthy scrape (``success=False``) rather than
    crashing the process.
    """
    started = time.monotonic()
    now = datetime.now(config.timezone)
    today = (now.year, now.month, now.day)

    try:
        config.validate()
        with FamilyLinkClient(config) as client:
            account_ids, names = _resolve_targets(config, client)
            children: list[ChildSnapshot] = []
            for account_id in account_ids:
                data = client.get_apps_and_usage(account_id)
                name = names.get(account_id, account_id)
                children.append(build_child_snapshot(account_id, name, data, today))

        snapshot = Snapshot(children=children, success=True)
        logger.info(
            "Collected %d child profile(s), %d app rows",
            len(children),
            sum(len(c.apps) for c in children),
        )
    except Exception as exc:  # noqa: BLE001 - surface as an unhealthy scrape
        logger.error("Collection failed: %s", exc, exc_info=logger.isEnabledFor(logging.DEBUG))
        snapshot = Snapshot(success=False, error=str(exc))

    snapshot.duration_seconds = time.monotonic() - started
    snapshot.timestamp = time.time()
    return snapshot
