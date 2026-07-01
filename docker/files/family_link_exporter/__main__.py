"""Command-line entrypoint: ``serve``, ``dump`` and ``login`` subcommands."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading

from prometheus_client import REGISTRY, start_http_server

from . import __version__
from .auth import AuthError
from .client import FamilyLinkClient
from .collector import collect_snapshot
from .config import Config
from .metrics import FamilyLinkCollector

logger = logging.getLogger("family_link_exporter")


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def _refresh_loop(
    config: Config,
    client: FamilyLinkClient,
    collector: FamilyLinkCollector,
    stop: threading.Event,
) -> None:
    """Poll the API every ``refresh_interval`` seconds until stopped."""
    while not stop.is_set():
        snapshot = collect_snapshot(config, client)
        collector.update(snapshot)
        stop.wait(config.refresh_interval)


def cmd_serve(config: Config) -> int:
    config.validate()
    client = FamilyLinkClient(config)
    collector = FamilyLinkCollector()
    REGISTRY.register(collector)

    stop = threading.Event()
    worker = threading.Thread(
        target=_refresh_loop, args=(config, client, collector, stop), daemon=True
    )
    worker.start()

    start_http_server(config.port, addr=config.host)
    logger.info(
        "Serving metrics on http://%s:%d/metrics (refresh every %ds)",
        config.host,
        config.port,
        config.refresh_interval,
    )

    def _handle_signal(signum, _frame):
        logger.info("Received signal %s, shutting down", signum)
        stop.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    stop.wait()
    worker.join(timeout=5)
    client.close()
    return 0


def cmd_dump(config: Config) -> int:
    """Fetch a single snapshot and print it as JSON (for debugging auth/data)."""
    config.validate()
    with FamilyLinkClient(config) as client:
        snapshot = collect_snapshot(config, client)
    json.dump(snapshot.to_dict(), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if snapshot.success else 1


def cmd_login(args: argparse.Namespace) -> int:
    from .login import interactive_login

    interactive_login(args.output, headless=args.headless)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="family-link-exporter")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Run the Prometheus exporter (default)")
    sub.add_parser("dump", help="Fetch once and print JSON, then exit")

    login = sub.add_parser("login", help="Interactively capture a Google session")
    login.add_argument(
        "-o", "--output", default="storage_state.json", help="Where to save the session"
    )
    login.add_argument(
        "--headless", action="store_true", help="Run the login browser headless"
    )

    args = parser.parse_args(argv)
    command = args.command or "serve"

    if command == "login":
        # login has no Config dependency; keep logging quiet-ish.
        _setup_logging("INFO")
        return cmd_login(args)

    try:
        config = Config.from_env()
        _setup_logging(config.log_level)
        if command == "dump":
            return cmd_dump(config)
        return cmd_serve(config)
    except (ValueError, AuthError) as exc:
        # Configuration / credential problems: report cleanly, no traceback.
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
