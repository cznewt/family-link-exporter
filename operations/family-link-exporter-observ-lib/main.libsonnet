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

    // Dashboard panel groups.
    local groups = [
      {
        title: 'Overview',
        width: 12,
        height: 6,
        elements: {
          up: s.up.asStat('Exporter up'),
          apps: s.apps.asStat('Apps tracked'),
          screen_time: s.screenTime.asTimeSeries('Screen time today (per child)'),
        },
      },
      {
        title: 'Usage & health',
        width: 12,
        height: 7,
        elements: {
          app_usage: s.appUsage.asTimeSeries('App usage today (per app)'),
          app_limit: s.appLimit.asTimeSeries('Configured daily limits'),
          scrape_duration: s.scrapeDuration.asTimeSeries('Scrape duration'),
        },
      },
    ];

    // All signals, for the pack .signals accessor.
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
              summary: 'family-link-exporter cannot reach the Kids Management API.',
              description: 'family_link_up is 0 on {{ $labels.instance }} (the Google session likely expired; refresh it).',
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
            record: 'instance:family_link_screen_time_seconds:sum',
            expr: 'sum by (instance) (family_link_screen_time_seconds{' + cfg.exporterSelector + '})',
          },
        ],
      },
    ];

    pack.build(cfg, allSignals, groups, alerts)
    + { prometheus+: { rules: rules } },
}
