# Deployment

## Helm (Kubernetes)

The chart is published to ghcr as an OCI artifact. The exporter needs a Google
session captured out-of-band (it cannot log in from inside the cluster).

```bash
# 1. Capture a parent session locally.
pip install playwright && playwright install chromium
python -m family_link_exporter login -o storage_state.json

# 2. Store it as a Secret.
kubectl create secret generic family-link-session \
  --from-file=storage_state.json=./storage_state.json

# 3. Install the chart.
helm install family-link oci://ghcr.io/cznewt/charts/family-link-exporter \
  --set auth.existingSecret=family-link-session \
  --set config.timezone=Europe/Prague
```

To scrape with the Prometheus Operator, enable the ServiceMonitor:

```bash
helm upgrade family-link oci://ghcr.io/cznewt/charts/family-link-exporter \
  --reuse-values --set serviceMonitor.enabled=true
```

See the [chart README](https://github.com/cznewt/family-link-exporter/tree/main/operations/family-link-exporter-helm-chart)
for all values.

## Docker Compose

```bash
python -m family_link_exporter login -o storage_state.json  # produces ./storage_state.json
FLE_TIMEZONE=Europe/Prague docker compose up -d
```

The bundled `docker-compose.yml` builds the image, mounts `./storage_state.json`
read-only, and serves metrics on port 9838.
