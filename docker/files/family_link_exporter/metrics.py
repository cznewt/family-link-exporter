"""Prometheus custom collector.

A background thread refreshes an in-memory :class:`Snapshot`; every Prometheus
scrape renders metric families from that cached snapshot. Building fresh metric
families each scrape (instead of long-lived Gauge objects) means apps that stop
reporting usage -- e.g. at the local midnight rollover -- simply disappear from
the output instead of getting stuck at a stale value.
"""

from __future__ import annotations

import threading

from prometheus_client.core import GaugeMetricFamily

from .collector import Snapshot

NAMESPACE = "family_link"


class FamilyLinkCollector:
    """A ``prometheus_client`` custom collector backed by a cached snapshot."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot = Snapshot()  # empty until the first collection

    def update(self, snapshot: Snapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def collect(self):
        with self._lock:
            snap = self._snapshot

        # --- Scrape health (per family) ------------------------------------- #
        up = GaugeMetricFamily(
            f"{NAMESPACE}_up",
            "1 if the last collection for this family succeeded.",
            labels=["family"],
        )
        scrape_duration = GaugeMetricFamily(
            f"{NAMESPACE}_scrape_duration_seconds",
            "Duration of the last collection for this family.",
            labels=["family"],
        )
        for f in snap.families:
            up.add_metric([f.name], 1.0 if f.success else 0.0)
            scrape_duration.add_metric([f.name], f.duration_seconds)
        yield up
        yield scrape_duration
        yield GaugeMetricFamily(
            f"{NAMESPACE}_last_scrape_timestamp_seconds",
            "Unix time of the last collection cycle.",
            value=snap.timestamp,
        )

        child_labels = ["family", "child", "account_id"]
        screen_time = GaugeMetricFamily(
            f"{NAMESPACE}_screen_time_seconds",
            "Total screen time used today (sum across apps and devices).",
            labels=child_labels,
        )
        apps_total = GaugeMetricFamily(
            f"{NAMESPACE}_apps_total",
            "Number of apps reported for the child.",
            labels=child_labels,
        )

        app_labels = ["family", "child", "account_id", "package", "app"]
        usage = GaugeMetricFamily(
            f"{NAMESPACE}_app_usage_seconds",
            "Per-app screen time used today.",
            labels=app_labels,
        )
        limit = GaugeMetricFamily(
            f"{NAMESPACE}_app_daily_limit_minutes",
            "Configured daily time limit for the app, in minutes (if any).",
            labels=app_labels,
        )
        blocked = GaugeMetricFamily(
            f"{NAMESPACE}_app_blocked",
            "1 if the app is blocked (hidden) for the child.",
            labels=app_labels,
        )
        always_allowed = GaugeMetricFamily(
            f"{NAMESPACE}_app_always_allowed",
            "1 if the app is always allowed (exempt from limits/downtime).",
            labels=app_labels,
        )

        device_labels = [
            "family", "child", "account_id", "device_id", "model", "friendly_name",
        ]
        device_activity = GaugeMetricFamily(
            f"{NAMESPACE}_device_last_activity_timestamp_seconds",
            "Unix time of the device's last reported activity.",
            labels=device_labels,
        )

        for fam in snap.families:
            for child in fam.children:
                cvals = [fam.name, child.name, child.account_id]
                screen_time.add_metric(cvals, child.total_usage_seconds)
                apps_total.add_metric(cvals, len(child.apps))

                for app in child.apps:
                    avals = [fam.name, child.name, child.account_id, app.package, app.title]
                    usage.add_metric(avals, app.usage_seconds)
                    blocked.add_metric(avals, 1.0 if app.blocked else 0.0)
                    always_allowed.add_metric(avals, 1.0 if app.always_allowed else 0.0)
                    if app.daily_limit_minutes is not None:
                        limit.add_metric(avals, app.daily_limit_minutes)

                for dev in child.devices:
                    if dev.last_activity_seconds is None:
                        continue
                    device_activity.add_metric(
                        [fam.name, child.name, child.account_id, dev.device_id,
                         dev.model, dev.friendly_name],
                        dev.last_activity_seconds,
                    )

        yield screen_time
        yield apps_total
        yield usage
        yield limit
        yield blocked
        yield always_allowed
        yield device_activity
