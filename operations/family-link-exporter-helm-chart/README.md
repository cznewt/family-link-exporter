# family-link-exporter Helm chart

Deploys the [family-link-exporter](https://github.com/cznewt/family-link-exporter)
— a read-only Prometheus exporter for Google Family Link screen-time usage and
parental-control settings.

## Install

The exporter needs a Google session captured out-of-band (it cannot log in from
inside the cluster). Capture one locally, store it as a Secret, then install:

```bash
# 1. Capture a parent Google session (opens a browser; do the 2FA).
pip install playwright && playwright install chromium
python -m family_link_exporter login -o storage_state.json

# 2. Create a Secret from it.
kubectl create secret generic family-link-session \
  --from-file=storage_state.json=./storage_state.json

# 3. Install the chart from ghcr OCI.
helm install family-link oci://ghcr.io/cznewt/charts/family-link-exporter \
  --set auth.existingSecret=family-link-session \
  --set config.timezone=Europe/Prague
```

Alternatively inline the session (creates the Secret for you):

```bash
helm install family-link oci://ghcr.io/cznewt/charts/family-link-exporter \
  --set-file auth.storageState=./storage_state.json
```

## Key values

| Key | Default | Description |
| --- | --- | --- |
| `image.repository` / `image.tag` | `ghcr.io/cznewt/family-link-exporter` / chart appVersion | Image |
| `auth.existingSecret` | `""` | Secret holding `storage_state.json` (preferred) |
| `auth.storageState` | `""` | Inline session JSON; chart creates the Secret |
| `auth.key` / `auth.mountPath` | `storage_state.json` / `/etc/family-link-exporter` | Mount location |
| `config.timezone` | `Europe/Prague` | Timezone for the daily "today" boundary |
| `config.refreshInterval` | `900` | Seconds between API polls |
| `config.accountIds` | `""` | Comma-separated child ids; empty = all supervised |
| `service.port` | `9838` | Metrics port |
| `serviceMonitor.enabled` | `false` | Create a Prometheus Operator ServiceMonitor |

Sessions expire — when `family_link_up` drops to `0`, refresh
`storage_state.json`, update the Secret, and restart the pod.

## Scrape without the Operator

If you are not using the Prometheus Operator, the pod carries
`prometheus.io/scrape` annotations, or add a static job:

```yaml
scrape_configs:
  - job_name: family_link
    static_configs:
      - targets: ["family-link-family-link-exporter.<namespace>.svc:9838"]
```
