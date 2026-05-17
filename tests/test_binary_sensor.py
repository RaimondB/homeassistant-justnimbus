"""Tests for the JustNimbus MQTT binary sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.justnimbus_mqtt.const import (
    DEFAULT_TOPIC_PREFIX,
    signal_message,
)


def _fire(hass: HomeAssistant, entry_id: str, topic: str, payload: str) -> None:
    async_dispatcher_send(hass, signal_message(entry_id), topic, payload)


async def test_binary_sensors_created(hass: HomeAssistant, loaded_entry) -> None:
    """All six binary sensors should be created."""
    states = hass.states.async_all("binary_sensor")
    assert len(states) == 6
    registry = er.async_get(hass)
    for key in (
        "overflow",
        "reservoir_full",
        "system_error",
        "pump_actuator",
        "valve_in_actuator",
        "valve_out_actuator",
    ):
        entity = registry.async_get_entity_id(
            "binary_sensor", "justnimbus_mqtt", f"{loaded_entry.entry_id}_{key}"
        )
        assert entity is not None, f"binary_sensor '{key}' not registered"


async def test_actuator_on_off(hass: HomeAssistant, loaded_entry) -> None:
    """'valvein.off' -> off, 'valvein.on' -> on."""
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "binary_sensor",
        "justnimbus_mqtt",
        f"{loaded_entry.entry_id}_valve_in_actuator",
    )

    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/actuator/valve/in",
        "valvein.off",
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"

    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/actuator/valve/in",
        "valvein.on",
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "on"


async def test_system_error_problem(hass: HomeAssistant, loaded_entry) -> None:
    """0 -> off (no problem); non-zero -> on."""
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "binary_sensor", "justnimbus_mqtt", f"{loaded_entry.entry_id}_system_error"
    )

    _fire(hass, loaded_entry.entry_id, f"{DEFAULT_TOPIC_PREFIX}/system/error", "0")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"

    _fire(hass, loaded_entry.entry_id, f"{DEFAULT_TOPIC_PREFIX}/system/error", "12")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "on"


async def test_reservoir_full_uses_default_height(
    hass: HomeAssistant, loaded_entry
) -> None:
    """Reservoir full triggers at the configured 500 mm height."""
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "binary_sensor", "justnimbus_mqtt", f"{loaded_entry.entry_id}_reservoir_full"
    )

    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/height",
        "499",
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"

    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/height",
        "500",
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "on"


async def test_overflow_on(hass: HomeAssistant, loaded_entry) -> None:
    """Payload 1 sets overflow to on."""
    _fire(hass, loaded_entry.entry_id, f"{DEFAULT_TOPIC_PREFIX}/sensor/overflow", "1")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "on"


async def test_overflow_off(hass: HomeAssistant, loaded_entry) -> None:
    """Payload 0 sets overflow to off."""
    _fire(hass, loaded_entry.entry_id, f"{DEFAULT_TOPIC_PREFIX}/sensor/overflow", "0")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "off"


async def test_overflow_float_payload(hass: HomeAssistant, loaded_entry) -> None:
    """Float payload 1.0 (as the device sends) is treated as on."""
    _fire(hass, loaded_entry.entry_id, f"{DEFAULT_TOPIC_PREFIX}/sensor/overflow", "1.0")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "on"


async def test_overflow_invalid_payload(hass: HomeAssistant, loaded_entry) -> None:
    """Invalid payload leaves state as unknown."""
    _fire(hass, loaded_entry.entry_id, f"{DEFAULT_TOPIC_PREFIX}/sensor/overflow", "bad")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "unknown"
