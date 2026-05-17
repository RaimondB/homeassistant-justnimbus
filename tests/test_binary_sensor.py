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


async def test_overflow_entity_created(hass: HomeAssistant, loaded_entry) -> None:
    """One binary sensor entity (overflow) should be created."""
    states = hass.states.async_all("binary_sensor")
    assert len(states) == 1
    registry = er.async_get(hass)
    entry = registry.async_get_entity_id(
        "binary_sensor", "justnimbus_mqtt", f"{loaded_entry.entry_id}_overflow"
    )
    assert entry is not None


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
