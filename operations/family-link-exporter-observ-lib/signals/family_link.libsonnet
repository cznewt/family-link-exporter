local signal = import 'libs/common-lib/signal/main.libsonnet';

// Signals for the family-link-exporter metrics. Filtered by the global $job
// selector so the dashboard's job variable scopes every panel.
function(cfg)
  local sel = cfg.selector;
  local sig(name, expr, unit='short') =
    signal.new(name, 'prometheus', cfg.datasource, expr, unit).filteringSelector(sel);
  {
    up: sig('Exporter up', 'family_link_up{%(queriesSelector)s}', 'short'),
    apps: sig('Apps tracked', 'family_link_apps_total{%(queriesSelector)s}', 'short'),
    screenTime: sig(
      'Screen time today',
      'family_link_screen_time_seconds{%(queriesSelector)s}',
      's',
    ),
    appUsage: sig(
      'App usage today',
      'family_link_app_usage_seconds{%(queriesSelector)s}',
      's',
    ),
    appLimit: sig(
      'App daily limit',
      'family_link_app_daily_limit_minutes{%(queriesSelector)s} * 60',
      's',
    ),
    scrapeDuration: sig(
      'Scrape duration',
      'family_link_scrape_duration_seconds{%(queriesSelector)s}',
      's',
    ),
  }
