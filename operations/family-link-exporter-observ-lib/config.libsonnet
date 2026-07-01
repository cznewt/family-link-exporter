// Default config for the family-link-exporter observ-viz pack.
// Override any field by passing it to main.new({ ... }).
{
  local this = self,

  uid: 'family-link-exporter',
  // The dashboard IS the "Android Device" board, placed directly in the
  // Parental Control folder.
  dashboardTitle: 'Android Device',
  dashboardTags: ['family-link-exporter', 'parental-control'],
  datasource: '${datasource}',

  // Grafana folder = the existing "Parental Control" folder (instance-specific
  // uid in the target Grafana; override for a different Grafana).
  folder: {
    uid: 'afqtbmnsbpb7ka',
    title: 'Parental Control',
  },

  // apps_total carries job+family+child and exists for every child, so it drives
  // the $job / $family / $child dropdowns.
  varMetric: 'family_link_apps_total',
  varLabels: ['family', 'child'],

  // Per-signal selectors: health metrics carry only `family`; per-child data
  // also carries `child`. Signals pick the matching one (see the signals file).
  familySelector: 'job=~"$job", family=~"$family"',
  childSelector: 'job=~"$job", family=~"$family", child=~"$child"',
  selector: 'job=~"$job", family=~"$family", child=~"$child"',

  // Static selector for ALERT expressions (alerts cannot use dashboard vars).
  exporterSelector: 'job="family-link-exporter"',

  // Alert tuning.
  downFor: '5m',
  unhealthyFor: '15m',
  staleSeconds: 3600,
  staleFor: '15m',

  signals: {
    family_link: (import './signals/family_link.libsonnet')(this),
  },
}
