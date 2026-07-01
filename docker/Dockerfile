# Prometheus exporter for Google Family Link.
#
# Reads screen-time usage and parental-control settings from Google's internal
# Kids Management API (the families.google.com backend) using a Google session
# captured out-of-band, and serves them on /metrics. See the repo README.
#
# The `login` subcommand (which needs Playwright) is a local/dev step and is
# deliberately NOT installed here — the running container only needs to `serve`.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY files/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY files/family_link_exporter /app/family_link_exporter

EXPOSE 9838

RUN useradd --create-home --uid 10001 exporter
USER exporter

ENTRYPOINT ["python", "-m", "family_link_exporter"]
CMD ["serve"]
