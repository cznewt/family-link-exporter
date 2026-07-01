// observ-viz pack for family-link-exporter (built on cznewt/observ-viz).
//
//   local p = (import 'main.libsonnet').new({});
//   p.grafana.dashboard      // a Grafana dashboard (.toSpec() for JSON)
//   p.asMonitoringMixin()    // { grafanaDashboards+, prometheusAlerts+ }
local pack = import 'libs/common-lib/pack.libsonnet';

{
  new(config={}):
    local cfg = (import 'config.libsonnet') + config;
    local s = cfg.signals.family_link;

    // Dashboard panel groups. Filter with the $family and $child dropdowns.
    local groups = [
      {
        title: 'Overview',
        width: 6,
        height: 6,
        elements: {
          up: s.up.asStat('Exporter up'),
          apps: s.apps.asStat('Apps tracked'),
          screen_time: s.screenTime.asTimeSeries('Screen time today (per child)'),
        },
      },
      {
        title: 'Apps',
        width: 12,
        height: 9,
        elements: {
          usage_by_app: s.usageByApp.asTable('Screen time today by app'),
          limit_by_app: s.limitByApp.asTable('Daily limits by app'),
        },
      },
      {
        title: 'Devices',
        width: 12,
        height: 7,
        elements: {
          usage_by_device: s.usageByDevice.asTimeSeries('Screen time today by device'),
          usage_by_device_table: s.usageByDevice.asTable('Screen time today by device'),
        },
      },
      {
        title: 'Health',
        width: 12,
        height: 6,
        elements: {
          scrape_duration: s.scrapeDuration.asTimeSeries('Scrape duration (per family)'),
        },
      },
    ];

    local allSignals = { ['family_link_' + k]: s[k] for k in std.objectFields(s) };

    local alerts = [
      {
        name: 'family-link-exporter',
        rules: [
          {
            alert: 'FamilyLinkExporterDown',
            expr: 'up{' + cfg.exporterSelector + '} == 0',
            'for': cfg.downFor,
            labels: { severity: 'critical' },
            annotations: {
              summary: 'family-link-exporter is down.',
              description: '{{ $labels.instance }} has been unreachable for more than ' + cfg.downFor + '.',
            },
          },
          {
            alert: 'FamilyLinkExporterUnhealthy',
            expr: 'family_link_up{' + cfg.exporterSelector + '} == 0',
            'for': cfg.unhealthyFor,
            labels: { severity: 'warning' },
            annotations: {
              summary: 'family-link-exporter cannot reach the Kids Management API for a family.',
              description: 'family_link_up is 0 for family {{ $labels.family }} on {{ $labels.instance }} (the Google session likely expired; refresh it).',
            },
          },
          {
            alert: 'FamilyLinkExporterScrapeStale',
            expr: 'time() - family_link_last_scrape_timestamp_seconds{' + cfg.exporterSelector + '} > ' + cfg.staleSeconds,
            'for': cfg.staleFor,
            labels: { severity: 'warning' },
            annotations: {
              summary: 'family-link-exporter data is stale.',
              description: 'No successful collection on {{ $labels.instance }} for over ' + cfg.staleSeconds + 's.',
            },
          },
        ],
      },
    ];

    local rules = [
      {
        name: 'family-link-exporter',
        rules: [
          {
            record: 'family:family_link_screen_time_seconds:sum',
            expr: 'sum by (family) (family_link_screen_time_seconds{' + cfg.exporterSelector + '})',
          },
        ],
      },
    ];

    pack.build(cfg, allSignals, groups, alerts)
    + { prometheus+: { rules: rules } },
}
