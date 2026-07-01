# Configuration

All settings are environment variables prefixed `FLE_`.

## Authentication

Set exactly one credential source. Each yields the Google session cookies; the
exporter derives a `SAPISIDHASH` Authorization header from them per request.

| Variable | Source | Best for |
| --- | --- | --- |
| `FLE_STORAGE_STATE` | Playwright `storage_state.json` from `... login` | Servers / containers (recommended) |
| `FLE_COOKIE_FILE` | Netscape `cookies.txt` exported from a browser | Manual / no Playwright |
| `FLE_COOKIE_BROWSER` | Cookies read live from a local browser (`firefox`, `chrome`, …) | Desktop only |

Capture a reusable session (2FA supported):

```bash
pip install playwright && playwright install chromium
python -m family_link_exporter login -o storage_state.json
```

Sessions expire. When `family_link_up` drops to `0`, re-run `login` (or refresh
the cookie file) and restart the exporter.

## Settings

| Variable | Default | Description |
| --- | --- | --- |
| `FLE_ACCOUNT_IDS` | *(all supervised)* | Comma-separated child account ids to export |
| `FLE_REFRESH_INTERVAL` | `900` | Seconds between Kids Management API polls |
| `FLE_TIMEZONE` | *(system)* | Timezone for the daily "today" boundary — set to the child's tz |
| `FLE_HOST` / `FLE_PORT` | `0.0.0.0` / `9838` | Metrics server bind address |
| `FLE_LOG_LEVEL` | `INFO` | Logging level |

## Commands

The container runs `serve` by default. All subcommands:

```bash
python -m family_link_exporter serve   # Prometheus exporter on FLE_PORT
python -m family_link_exporter dump    # fetch once, print JSON, exit (debug auth/data)
python -m family_link_exporter login   # capture a Google session (needs Playwright)
```
