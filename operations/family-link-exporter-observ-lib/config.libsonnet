// Default config for the family-link-exporter observ-viz pack.
// Override any field by passing it to main.new({ ... }).
{
  local this = self,

  uid: 'family-link-exporter',
  dashboardTitle: 'Family Link Exporter',
  dashboardTags: ['family-link-exporter'],
  datasource: '${datasource}',

  // Dashboard query selector, driven by the $job and $family variables.
  selector: 'job=~"$job", family=~"$family"',
  varMetric: 'family_link_up',
  // Cascading filter variable: a $family dropdown (label_values on family).
  varLabels: ['family'],

  // Static selector for ALERT expressions (alerts cannot use the $job var).
  exporterSelector: 'job="family-link-exporter"',

  // Alert tuning.
  downFor: '5m',      // Prometheus target unreachable
  unhealthyFor: '15m',  // family_link_up == 0 (auth/session problem)
  staleSeconds: 3600,   // last successful scrape older than this
  staleFor: '15m',

  // Signals for the exporter's metrics.
  signals: {
    family_link: (import './signals/family_link.libsonnet')(this),
  },
}
