# homeassistant-justnimbus

[![Validate](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/validate.yml/badge.svg)](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/validate.yml)
[![CI](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/ci.yml/badge.svg)](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/ci.yml)

Home Assistant custom integration for **JustNimbus** rainwater pumps, using local MQTT for real-time updates — no cloud polling, no internet dependency.

## Features

- **Local push** (`iot_class: local_push`) — connects **directly** to your
  MQTT broker via `aiomqtt`; no cloud, no polling, and **no dependency on
  Home Assistant's MQTT integration**
- Full coverage of the device's MQTT topics: water pressure / temperature /
  volume / height, flow in & out, hourly / 24 h / total water used & added,
  pump statistics (starts, runtime), and system status / mode
- Binary sensors: overflow, reservoir full, system error (problem), and
  pump / valve-in / valve-out actuators
- Derived **reservoir fill %** and **reservoir full** from the configured
  reservoir ("zak") dimensions — pick a standard bag, Custom, or Unknown
- `water used/added (total)` use the `water` device class, so they feed the
  **Energy → Water** dashboard; state is restored across restarts
- Configurable broker host/port, topic prefix (default: `justnimbus`),
  device name, and reservoir — all from the UI

## Prerequisites

- A JustNimbus device publishing to an MQTT broker reachable from Home
  Assistant (the device's embedded broker, or any broker it publishes to)
- The broker's host and port — entered during setup

> Home Assistant's own MQTT integration is **not** required; this
> integration owns its own broker connection.

## Installation (HACS)

1. Add this repository as a custom HACS repository (category: **Integration**)
2. Install **JustNimbus MQTT**
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → JustNimbus MQTT**
5. Enter the broker **host** and **port**, the **topic prefix** (default:
   `justnimbus`), and a **device name**
6. Choose the reservoir: a standard bag, **Custom** dimensions, or
   **Unknown** (skip — the fill / full entities stay unavailable until set
   later via the device's **Configure** button)

## Manual installation

Copy `custom_components/justnimbus_mqtt/` into your `<config>/custom_components/` directory and restart Home Assistant.

## Example dashboard

[`examples/dashboard.yaml`](examples/dashboard.yaml) recreates the device's
own POMP / BUFFER / BIJVULLEN dashboard from the integration's entities.
Paste it into a new dashboard's raw configuration; adjust the entity-id
prefix if your device name isn't the default `JustNimbus`.

## Development

```bash
scripts/ci          # lint + format check + tests
scripts/ci fix      # auto-fix lint/format issues
scripts/ci test     # tests only
```

See [docs/CI.md](docs/CI.md) for the full CI workflow and the pre-push
checklist (verify the PR isn't merged, run local CI, then push).

### Probing a real device (no Home Assistant)

`scripts/probe` connects to the JustNimbus MQTT broker exactly like the
integration does, dumps every message under `<prefix>/#`, and reports which
topics the integration *expects* were actually seen — so the topic→entity
mapping can be validated independently of the HA runtime.

```bash
JUSTNIMBUS_HOST=192.168.1.50 scripts/probe          # capture 30s + report
scripts/probe --duration 120                         # listen longer
scripts/probe --debug                                # verbose
```

Connection settings come from `JUSTNIMBUS_HOST` / `JUSTNIMBUS_PORT` (default
1883) / `JUSTNIMBUS_TOPIC_PREFIX` (default `justnimbus`), or a gitignored
`scripts/.justnimbus.env` with `KEY=VALUE` lines. It uses an isolated
`.venv-probe` (only `aiomqtt`), so it never collides with the test venv.

## License

MIT
