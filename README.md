# family-link-exporter

A **read-only Prometheus exporter** for [Google Family Link](https://families.google/familylink/).
It pulls each supervised child's **daily app usage** and **parental-control
settings** and exposes them as Prometheus metrics for Grafana.

```
Family Link  ──►  Kids Management API  ──►  exporter (/metrics)  ──►  Prometheus  ──►  Grafana
 (your data)        (unofficial)            this project
```

Image: `ghcr.io/cznewt/family-link-exporter` · Chart: `oci://ghcr.io/cznewt/charts/family-link-exporter`

## ⚠️ Read this first

- **There is no official Family Link API.** This talks to the *undocumented*
  internal `kidsmanagement-pa.clients6.google.com` endpoint that the
  [families.google.com](https://familylink.google.com) web app uses. It can
  change or break without notice, and automating it may be against Google's ToS.
  Use it only to export **your own family's** data.
- **Granularity is per-app, per-day.** The API's "usage sessions" are daily
  rollups, **not** an event stream — there are no per-open/close timestamps.
  True event-level data (app foreground/background, screen on/off) only exists
  on the child's device via Android's `UsageStatsManager` (a different project).
- **It is read-only.** The exporter only issues `GET` requests; it never changes
  limits, blocks, or any setting.

## Metrics

Per supervised child, refreshed every `FLE_REFRESH_INTERVAL` seconds:

| Metric | Labels | Meaning |
| --- | --- | --- |
| `family_link_app_usage_seconds` | child, account_id, package, app | Per-app screen time **today** (summed across devices) |
| `family_link_screen_time_seconds` | child, account_id | Total screen time today |
| `family_link_app_daily_limit_minutes` | child, account_id, package, app | Configured daily limit (only when set) |
| `family_link_app_blocked` | child, account_id, package, app | `1` if blocked |
| `family_link_app_always_allowed` | child, account_id, package, app | `1` if always allowed |
| `family_link_apps_total` | child, account_id | Number of apps reported |
| `family_link_device_last_activity_timestamp_seconds` | child, account_id, device_id, model, friendly_name | Device last-seen time |
| `family_link_up` | — | `1` if the last API collection succeeded |
| `family_link_scrape_duration_seconds`, `family_link_last_scrape_timestamp_seconds` | — | Scrape health |

> **Timezone note:** "today" is decided in `FLE_TIMEZONE` (default system local).
> Set it to the child's timezone so the daily rollover lines up.

## Quick start (Docker)

The exporter needs a logged-in Google session. Capture one once, then run:

```bash
# 1. Capture a parent Google session (opens a browser; do the 2FA).
pip install playwright && playwright install chromium
python -m family_link_exporter login -o storage_state.json

# 2. Run the published image.
docker run --rm -p 9838:9838 \
  -e FLE_STORAGE_STATE=/session/storage_state.json \
  -e FLE_TIMEZONE=Europe/Prague \
  -v "$PWD/storage_state.json:/session/storage_state.json:ro" \
  ghcr.io/cznewt/family-link-exporter:latest

curl -s localhost:9838/metrics | grep family_link_
```

Or use the bundled stack: `FLE_TIMEZONE=Europe/Prague docker compose up -d --build`.

## Kubernetes (Helm)

```bash
kubectl create secret generic family-link-session \
  --from-file=storage_state.json=./storage_state.json

helm install family-link oci://ghcr.io/cznewt/charts/family-link-exporter \
  --set auth.existingSecret=family-link-session \
  --set config.timezone=Europe/Prague
```

See [`operations/family-link-exporter-helm-chart`](operations/family-link-exporter-helm-chart/README.md).

## Authentication

Set exactly one credential source (see [docs/configuration.md](docs/configuration.md)):

| Env var | Source | Best for |
| --- | --- | --- |
| `FLE_STORAGE_STATE` | Playwright `storage_state.json` from `... login` | **Servers / containers** (recommended) |
| `FLE_COOKIE_FILE` | Netscape `cookies.txt` from your browser | Manual/no-Playwright |
| `FLE_COOKIE_BROWSER` | Cookies read live from a local browser via `browser_cookie3` | Desktop only |

Sessions expire — when `family_link_up` goes to `0`, refresh the session and
restart the exporter.

### If Google blocks the Playwright login

Google shows *"This browser or app may not be secure"* for automated Chromium.
Two ways around it:

1. **Drive your real browser** instead of bundled Chromium:
   ```bash
   playwright install chrome
   python -m family_link_exporter login --channel chrome -o storage_state.json
   ```
2. **Export cookies** from a browser you're already logged into (most reliable):
   open <https://familylink.google.com> as the parent, use a *"Get cookies.txt
   LOCALLY"* extension to save `cookies.txt`, then use it directly —
   `FLE_COOKIE_FILE=cookies.txt python -m family_link_exporter dump`. In the
   chart, set `auth.mode=cookieFile`, `auth.key=cookies.txt` and put the file in
   the Secret.

## Repository layout

```
docker/
  Dockerfile                       # slim runtime image (serve)
  files/
    requirements.txt
    family_link_exporter/          # the Python package
operations/
  family-link-exporter-helm-chart/ # Helm chart (published to ghcr OCI)
.github/workflows/                 # build (image), ci, publish-helm-charts, docs
tests/                             # offline tests (no Google account needed)
VERSION                            # image + chart appVersion tag
```

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r docker/files/requirements.txt pytest
pytest -q          # offline tests — no Google account needed

# Run locally against a real session:
export FLE_STORAGE_STATE=./storage_state.json FLE_TIMEZONE=Europe/Prague
python -m family_link_exporter dump    # fetch once, print JSON
python -m family_link_exporter serve   # http://localhost:9838/metrics
```

## Credits

The Kids Management API auth approach (SAPISIDHASH over browser cookies) is based
on [`tducret/familylink`](https://github.com/tducret/familylink); the Home
Assistant [HAFamilyLink](https://github.com/Vortitron/HAFamilyLink) project
demonstrates the Playwright login pattern.

## License

MIT
