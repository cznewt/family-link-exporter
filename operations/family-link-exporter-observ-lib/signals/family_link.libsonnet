local signal = import 'libs/common-lib/signal/main.libsonnet';

// Signals for the family-link-exporter metrics. Health metrics filter on the
// family-only selector; per-child data also filters on $child.
function(cfg)
  local sig(name, expr, unit, sel) =
    signal.new(name, 'prometheus', cfg.datasource, expr, unit).filteringSelector(sel);
  {
    // Health (family granularity)
    up: sig('Exporter up', 'family_link_up{%(queriesSelector)s}', 'short', cfg.familySelector),
    scrapeDuration: sig(
      'Scrape duration',
      'family_link_scrape_duration_seconds{%(queriesSelector)s}',
      's',
      cfg.familySelector,
    ),

    // Per-child data
    apps: sig(
      'Apps tracked',
      'family_link_apps_total{%(queriesSelector)s}',
      'short',
      cfg.childSelector,
    ),
    screenTime: sig(
      'Screen time today',
      'family_link_screen_time_seconds{%(queriesSelector)s}',
      's',
      cfg.childSelector,
    ),
    usageByApp: sig(
      'Screen time today by app',
      'sum by (family, child, app) (family_link_app_usage_seconds{%(queriesSelector)s})',
      's',
      cfg.childSelector,
    ),
    limitByApp: sig(
      'Daily limit by app',
      'family_link_app_daily_limit_minutes{%(queriesSelector)s} * 60',
      's',
      cfg.childSelector,
    ),
    usageByDevice: sig(
      'Screen time today by device',
      'sum by (family, child, device) (family_link_app_device_usage_seconds{%(queriesSelector)s})',
      's',
      cfg.childSelector,
    ),
  }
