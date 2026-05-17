# homeassistant-justnimbus

[![Validate](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/validate.yml/badge.svg)](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/validate.yml)
[![CI](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/ci.yml/badge.svg)](https://github.com/RaimondB/homeassistant-justnimbus/actions/workflows/ci.yml)

Home Assistant custom integration for **JustNimbus** rainwater pumps, using local MQTT for real-time updates — no cloud polling, no internet dependency.

## Features

- **Local push** (`iot_class: local_push`) — state changes appear instantly via MQTT
- 12 sensor entities covering reservoir state, flow, pressure, temperature, and daily/hourly/total statistics
- 1 binary sensor for reservoir overflow detection
- Configurable topic prefix (default: `justnimbus`) and device name

## MQTT topics

The integration subscribes to the following topics under the configured prefix:

| Topic suffix | Entity | Unit |
|---|---|---|
| `sensor/water/pressure` | Pump pressure | bar |
| `sensor/water/temp` | Reservoir temperature | °C |
| `sensor/water/volume` | Reservoir volume | L |
| `sensor/water/height` | Water height | mm |
| `sensor/waterflow/in` | Water flow in | L/min |
| `sensor/waterflow/out` | Water flow out | L/min |
| `sensor/overflow` | Overflow (binary) | — |
| `stats/water/used/hour` | Water used (last hour) | L |
| `stats/water/used/24h` | Water used (24 h) | L |
| `stats/water/used/total` | Water used (total) | L |
| `stats/water/added/hour` | Water added (last hour) | L |
| `stats/water/added/24h` | Water added (24 h) | L |
| `stats/water/added/total` | Water added (total) | L |

## Prerequisites

1. A JustNimbus device publishing MQTT to your local broker
2. The [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) configured in Home Assistant

## Installation (HACS)

1. Add this repository as a custom HACS repository (category: **Integration**)
2. Install **JustNimbus MQTT**
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → JustNimbus MQTT**
5. Enter the topic prefix (default: `justnimbus`) and a device name

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
