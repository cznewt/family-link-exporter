"""Offline tests for the parsing/normalization logic (no network, no creds).

These exercise the exact response shape the Kids Management API returns so the
data pipeline can be verified without a Google account.
"""

from __future__ import annotations

from family_link_exporter.collector import (
    FamilySnapshot,
    Snapshot,
    build_child_snapshot,
    collect_snapshot,
)
from family_link_exporter.config import Config, Family
from family_link_exporter.metrics import FamilyLinkCollector
from family_link_exporter.models import AppUsage

SAMPLE = {
    "apps": [
        {
            "packageName": "com.spotify.music",
            "title": "Spotify",
            "supervisionSetting": {"usageLimit": {"dailyUsageLimitMins": 60, "enabled": True}},
        },
        {
            "packageName": "com.google.android.youtube",
            "title": "YouTube",
            "supervisionSetting": {"hidden": True},
        },
        {
            "packageName": "com.duolingo",
            "title": "Duolingo",
            "supervisionSetting": {
                "alwaysAllowedAppInfo": {"alwaysAllowedState": "alwaysAllowedStateEnabled"}
            },
        },
    ],
    "deviceInfo": [
        {
            "deviceId": "device-1",
            "displayInfo": {
                "model": "Pixel 7",
                "friendlyName": "Kid's phone",
                "lastActivityTimeMillis": "1719830000000",
            },
        }
    ],
    "appUsageSessions": [
        {"usage": "1800s", "appId": {"androidAppPackageName": "com.spotify.music"},
         "deviceMudId": "m1", "date": {"year": 2026, "month": 7, "day": 1}},
        {"usage": "600.5s", "appId": {"androidAppPackageName": "com.spotify.music"},
         "deviceMudId": "m2", "date": {"year": 2026, "month": 7, "day": 1}},
        {"usage": "300s", "appId": {"androidAppPackageName": "com.duolingo"},
         "date": {"year": 2026, "month": 7, "day": 1}},
        # Yesterday — must be excluded from "today".
        {"usage": "9999s", "appId": {"androidAppPackageName": "com.spotify.music"},
         "date": {"year": 2026, "month": 6, "day": 30}},
    ],
}

TODAY = (2026, 7, 1)


def _child():
    data = AppUsage.model_validate(SAMPLE)
    return build_child_snapshot("acc-1", "Alex", data, TODAY)


def test_usage_summed_across_devices_for_today_only():
    child = _child()
    spotify = next(a for a in child.apps if a.package == "com.spotify.music")
    # 1800 + 600.5 today; the 9999 from yesterday is excluded.
    assert spotify.usage_seconds == 1800 + 600.5


def test_settings_are_parsed():
    child = _child()
    by_pkg = {a.package: a for a in child.apps}
    assert by_pkg["com.spotify.music"].daily_limit_minutes == 60
    assert by_pkg["com.spotify.music"].limit_enabled is True
    assert by_pkg["com.google.android.youtube"].blocked is True
    assert by_pkg["com.duolingo"].always_allowed is True


def test_total_and_device():
    child = _child()
    assert child.total_usage_seconds == 1800 + 600.5 + 300
    assert child.devices[0].last_activity_seconds == 1719830000.0


def test_collector_renders_metrics():
    snapshot = Snapshot(
        families=[FamilySnapshot(name="smith", success=True, children=[_child()])],
        timestamp=1.0,
    )
    collector = FamilyLinkCollector()
    collector.update(snapshot)

    samples = {}
    for family in collector.collect():
        for sample in family.samples:
            samples.setdefault(sample.name, []).append(sample)

    up = {s.labels["family"]: s.value for s in samples["family_link_up"]}
    assert up["smith"] == 1.0
    usage = {s.labels["package"]: s.value for s in samples["family_link_app_usage_seconds"]}
    assert usage["com.spotify.music"] == 2400.5
    screen = {
        (s.labels["family"], s.labels["child"]): s.value
        for s in samples["family_link_screen_time_seconds"]
    }
    assert screen[("smith", "Alex")] == 2700.5


def test_collect_snapshot_without_credentials_is_unhealthy():
    # A family with no credential source -> that family reports unhealthy, no crash.
    snapshot = collect_snapshot(Config(families=[Family(name="nocreds")]))
    fam = snapshot.families[0]
    assert fam.success is False
    assert "credential" in (fam.error or "").lower()
