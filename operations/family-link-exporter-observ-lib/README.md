# family-link-exporter-observ-lib

An [observ-viz](https://github.com/cznewt/observ-viz) pack for
family-link-exporter: a Grafana dashboard plus Prometheus alerts and recording
rules for the `family_link_*` metrics.

## Rendered outputs (committed)

| Path | Contents |
| --- | --- |
| `dashboards/family-link-exporter.json` | Grafana dashboard (schema v2): exporter health, screen time per child, per-app usage, limits, scrape duration |
| `alerts/family-link-exporter.yaml` | `FamilyLinkExporterDown`, `FamilyLinkExporterUnhealthy`, `FamilyLinkExporterScrapeStale` |
| `rules/family-link-exporter.yaml` | `instance:family_link_screen_time_seconds:sum` recording rule |

## Rebuild

Rendered through the `ghcr.io/cznewt/observ-lib` image (observ-viz on the jpath,
no local `jsonnet`/`jb` needed):

```bash
just observ-lib-build      # from the repo root
```

Edit the sources — `config.libsonnet`, `signals/family_link.libsonnet`,
`main.libsonnet` — then re-render. CI (`observ-lib.yml`) fails if the committed
outputs drift from the sources.

## Use

- **Dashboard**: push it to Grafana with `just grafana-push` (set `GRAFANA_URL`
  + `GRAFANA_TOKEN` [+ `GRAFANA_NAMESPACE`] in `.env` — see `.env.example`).
  This POSTs the v2 resource to the app-platform API, the same way observ-viz's
  `scripts/load.py` does. Or import `dashboards/family-link-exporter.json`
  manually. It expects `datasource` and `job` template variables.
- **Alerts / rules**: load the YAML into Prometheus/Mimir (or Grafana-managed
  rules). The alerts scope to `job="family-link-exporter"` — adjust
  `exporterSelector` in `config.libsonnet` if your scrape job differs.
