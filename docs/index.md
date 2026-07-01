# Family Link Exporter

A **read-only Prometheus exporter** for [Google Family Link](https://families.google/familylink/).
It pulls each supervised child's **daily app usage** and **parental-control
settings** and exposes them as Prometheus metrics for Grafana.

```
Family Link  ->  Kids Management API  ->  exporter (/metrics)  ->  Prometheus  ->  Grafana
```

!!! warning "Unofficial, and per-day granularity"
    There is no official Family Link API. This talks to the *undocumented*
    internal `kidsmanagement-pa.clients6.google.com` endpoint the
    families.google.com web app uses; it can change without notice. Use it only
    to export **your own family's** data. The API exposes per-app, **per-day**
    usage totals — not a per-open/close event stream. It is read-only: the
    exporter never changes any Family Link setting.

## Metrics

| Metric | Labels | Meaning |
| --- | --- | --- |
| `family_link_app_usage_seconds` | child, account_id, package, app | Per-app screen time today |
| `family_link_screen_time_seconds` | child, account_id | Total screen time today |
| `family_link_app_daily_limit_minutes` | child, account_id, package, app | Configured daily limit |
| `family_link_app_blocked` | child, account_id, package, app | `1` if blocked |
| `family_link_app_always_allowed` | child, account_id, package, app | `1` if always allowed |
| `family_link_apps_total` | child, account_id | Apps reported |
| `family_link_device_last_activity_timestamp_seconds` | child, account_id, device_id, model, friendly_name | Device last-seen time |
| `family_link_up` | — | `1` if the last collection succeeded |
| `family_link_scrape_duration_seconds`, `family_link_last_scrape_timestamp_seconds` | — | Scrape health |

## Quick start

```bash
# Capture a parent Google session (browser + 2FA), then run the container.
pip install playwright && playwright install chromium
python -m family_link_exporter login -o storage_state.json

docker run --rm -p 9838:9838 \
  -e FLE_STORAGE_STATE=/session/storage_state.json \
  -e FLE_TIMEZONE=Europe/Prague \
  -v "$PWD/storage_state.json:/session/storage_state.json:ro" \
  ghcr.io/cznewt/family-link-exporter:latest

curl -s localhost:9838/metrics | grep family_link_
```

See [Configuration](configuration.md) for all options and
[Deployment](helm.md) for Kubernetes/Helm.
