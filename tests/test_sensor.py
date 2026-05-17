"""Tests for the JustNimbus MQTT sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.justnimbus_mqtt.const import (
    DEFAULT_TOPIC_PREFIX,
    signal_message,
)


def _entity_id(
    hass: HomeAssistant, entry_id: str, key: str, domain: str = "sensor"
) -> str:
    """Look up entity_id by unique_id via the entity registry."""
    registry = er.async_get(hass)
    unique_id = f"{entry_id}_{key}"
    entity_id = registry.async_get_entity_id(domain, "justnimbus_mqtt", unique_id)
    assert entity_id is not None, f"Entity '{key}' not found in registry"
    return entity_id


def _fire(hass: HomeAssistant, entry_id: str, topic: str, payload: str) -> None:
    """Helper: fire the dispatcher as the MQTT loop would."""
    async_dispatcher_send(hass, signal_message(entry_id), topic, payload)


async def test_sensor_count(hass: HomeAssistant, loaded_entry) -> None:
    """Twelve sensor entities should be created."""
    assert len(hass.states.async_all("sensor")) == 12


async def test_entity_ids_are_readable(hass: HomeAssistant, loaded_entry) -> None:
    """entity_ids derive from the key, never the device_class fallback."""
    entity_ids = {s.entity_id for s in hass.states.async_all("sensor")}
    assert "sensor.justnimbus_water_added_total" in entity_ids
    assert "sensor.justnimbus_pump_pressure" in entity_ids
    # No device_class fallback ("..._volume", "..._volume_7", ...).
    assert not any(
        "_volume" in eid and eid.rsplit("_", 1)[-1].isdigit() for eid in entity_ids
    )


async def test_pump_pressure_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Sensor state updates when a dispatcher message arrives."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/pressure",
        "1.8",
    )
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "pump_pressure"))
    assert state.state == "1.8"


async def test_reservoir_temp_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Reservoir temperature sensor updates correctly."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/temp",
        "14.5",
    )
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "reservoir_temp"))
    assert state.state == "14.5"


async def test_waterflow_in_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Water flow in sensor updates correctly."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/waterflow/in",
        "3.2",
    )
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "waterflow_in"))
    assert state.state == "3.2"


async def test_water_used_total_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Total water used statistic updates correctly."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/stats/water/used/total",
        "12345.0",
    )
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "water_used_total"))
    assert state.state == "12345.0"


async def test_invalid_payload_ignored(hass: HomeAssistant, loaded_entry) -> None:
    """Non-numeric payload leaves state as unknown rather than crashing."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/pressure",
        "bad",
    )
    await hass.async_block_till_done()

    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "pump_pressure"))
    assert state.state == "unknown"


async def test_wrong_topic_ignored(hass: HomeAssistant, loaded_entry) -> None:
    """Message on an unrelated topic does not change the sensor state."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/pressure",
        "1.5",
    )
    await hass.async_block_till_done()

    # Fire a message for a different topic — temperature should stay unknown
    temp_state = hass.states.get(
        _entity_id(hass, loaded_entry.entry_id, "reservoir_temp")
    )
    assert temp_state.state == "unknown"
