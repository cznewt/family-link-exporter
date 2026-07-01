"""Prometheus exporter for Google Family Link.

Reads screen-time usage and parental-control settings from Google's internal
Kids Management API (the same backend the families.google.com web app uses) and
exposes them as Prometheus metrics for Grafana.

This project talks to an *undocumented* Google endpoint. There is no official
Family Link API; the endpoint can change without notice. Use it only to export
your own family's data.
"""

__version__ = "0.1.0"
