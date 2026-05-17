# ADR 0001: Use aiomqtt 2.x and retain MQTT 3.1.1 compatibility

**Date:** 2026-05-17
**Status:** Accepted

## Context

The integration needs an async MQTT client library. Three options were on the table:

- **paho-mqtt** directly — synchronous/threaded; doesn't fit HA's async model
- **aiomqtt 2.x** — async wrapper around paho-mqtt; supports MQTTv3.1.1 and MQTTv5
- **aiomqtt 3.x** — rewrites the backend in Rust (mqtt5 crate); pure asyncio, **MQTTv5 only**

aiomqtt 3.x drops MQTTv3.1.1 support entirely. The JustNimbus rainwater pump uses a local MQTT broker that speaks MQTTv3.1.1; there is no evidence the firmware supports MQTTv5.

There is also a dependency conflict on Python 3.12: phacc (the HA custom-component test harness) 0.13.205 pins `paho-mqtt==1.6.1`, while aiomqtt 2.x requires `paho-mqtt>=2.1.0`. This conflict is resolved on Python 3.13+ where phacc 0.13.206+ uses `paho-mqtt==2.1.0`.

## Decision

Use **aiomqtt 2.x** and keep **MQTTv3.1.1** compatibility.

For the Python 3.12 test environment, stub aiomqtt in `sys.modules` so it never needs to be installed alongside phacc 0.13.205.

## Consequences

- The integration works with any standard MQTT 3.1.1 broker (Mosquitto, the JustNimbus device, etc.)
- aiomqtt 3.x migration is deferred until the device firmware is confirmed to support MQTTv5
- On Python 3.12, the test `sys.modules` stub must be maintained; upgrading the dev environment to Python 3.13+ and phacc 0.13.206+ removes the conflict and the stub
