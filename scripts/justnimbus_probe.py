#!/usr/bin/env python3
"""Standalone JustNimbus MQTT probe — no Home Assistant required.

Connects to the JustNimbus device's MQTT broker exactly like the integration
does (aiomqtt, subscribe to ``<prefix>/#``), prints every message it sees,
and then reports which topics the integration *expects* were actually seen —
so the topic->entity mapping can be validated independently of the Home
Assistant runtime.

Connection settings come from the environment (never hard-code / commit a
broker that isn't yours):

    JUSTNIMBUS_HOST          (required)
    JUSTNIMBUS_PORT          (default 1883)
    JUSTNIMBUS_TOPIC_PREFIX  (default "justnimbus")

or a gitignored ./scripts/.justnimbus.env file with KEY=VALUE lines.

Usage:
    scripts/probe                       # capture for 30s, then coverage report
    scripts/probe --duration 120        # listen longer (slow-publishing device)
    scripts/probe --debug               # + verbose logging
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import pathlib
import re
import sys

import aiomqtt

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_INTEGRATION = _ROOT / "custom_components" / "justnimbus_mqtt"

_DEFAULT_PORT = 1883
_DEFAULT_PREFIX = "justnimbus"


def _load_config() -> tuple[str, int, str]:
    """Resolve broker host/port/prefix from env or ./scripts/.justnimbus.env."""
    here = pathlib.Path(__file__).resolve().parent
    for env_file in (here / ".justnimbus.env", _ROOT / ".justnimbus.env"):
        if env_file.exists():
            print(f"==> Loading config from {env_file}")
            for raw in env_file.read_text().splitlines():
                line = raw.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))
            break

    host = os.environ.get("JUSTNIMBUS_HOST")
    if not host:
        sys.exit(
            "Missing JUSTNIMBUS_HOST. Set JUSTNIMBUS_HOST (and optionally "
            "JUSTNIMBUS_PORT / JUSTNIMBUS_TOPIC_PREFIX), or create "
            "./scripts/.justnimbus.env."
        )
    port = int(os.environ.get("JUSTNIMBUS_PORT", _DEFAULT_PORT))
    prefix = os.environ.get("JUSTNIMBUS_TOPIC_PREFIX", _DEFAULT_PREFIX)
    return host, port, prefix


def _expected_suffixes() -> set[str]:
    """Parse the topic suffixes the integration maps, straight from source.

    Read with regex (no import — the platform modules pull in Home Assistant)
    so this stays correct without duplicating the mapping or drifting.
    """
    suffixes: set[str] = set()
    sensor_src = (_INTEGRATION / "sensor.py").read_text()
    suffixes.update(re.findall(r'topic_suffix\s*=\s*"([^"]+)"', sensor_src))
    binary_src = (_INTEGRATION / "binary_sensor.py").read_text()
    suffixes.update(re.findall(r'_OVERFLOW_TOPIC_SUFFIX\s*=\s*"([^"]+)"', binary_src))
    if not suffixes:
        sys.exit("!! Could not parse any expected topic suffixes from source.")
    return suffixes


async def _run(duration: float) -> int:
    host, port, prefix = _load_config()
    expected = {f"{prefix}/{s}" for s in _expected_suffixes()}
    wildcard = f"{prefix}/#"

    seen: dict[str, str] = {}
    print(f"==> Connecting to {host}:{port}, subscribing to {wildcard!r}")
    try:
        async with aiomqtt.Client(hostname=host, port=port) as client:
            print(
                f"==> Connected. Capturing for {duration:.0f}s "
                "(Ctrl-C to stop early) ...\n"
            )
            await client.subscribe(wildcard)

            async def _consume() -> None:
                async for msg in client.messages:
                    topic = str(msg.topic)
                    payload = msg.payload.decode(errors="replace")
                    if topic not in seen:
                        print(f"  [new] {topic} = {payload}")
                    seen[topic] = payload

            try:
                await asyncio.wait_for(_consume(), timeout=duration)
            except TimeoutError:
                pass
    except aiomqtt.MqttError as err:
        print(f"!! MQTT connection failed: {type(err).__name__}: {err}")
        return 2
    except KeyboardInterrupt:
        print("\n==> Stopped by user.")

    return _report(expected, seen)


def _report(expected: set[str], seen: dict[str, str]) -> int:
    print(f"\n==> Captured {len(seen)} distinct topic(s).\n")
    print("--- Integration topic coverage ---")
    missing = sorted(expected - seen.keys())
    for topic in sorted(expected):
        if topic in seen:
            print(f"  OK    {topic} = {seen[topic]}")
        else:
            print(f"  MISS  {topic}  (no message received)")

    extra = sorted(seen.keys() - expected)
    if extra:
        print("\n--- Published but NOT mapped by the integration ---")
        for topic in extra:
            print(f"  ----  {topic} = {seen[topic]}")

    if missing:
        print(
            f"\n!! {len(missing)} expected topic(s) never arrived — the "
            "mapping or prefix may be wrong, or the device was idle."
        )
        return 3
    print("\n==> All expected topics observed. Mapping looks correct.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe a JustNimbus MQTT broker.")
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="seconds to capture before reporting (default 30)",
    )
    parser.add_argument("--debug", action="store_true", help="enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    raise SystemExit(asyncio.run(_run(args.duration)))


if __name__ == "__main__":
    main()
