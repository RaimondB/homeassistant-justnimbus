"""Tests for the JustNimbus MQTT binary sensor platform."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_fire_mqtt_message


@pytest.fixture
async def loaded_entry(hass: HomeAssistant, config_entry, mqtt_mock):
    """Set up the integration and wait for entities to register."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_overflow_entity_created(hass: HomeAssistant, loaded_entry) -> None:
    """One binary sensor entity (overflow) should be created."""
    states = hass.states.async_all("binary_sensor")
    assert len(states) == 1
    # Entity ID is derived from device class (moisture), not the translation key
    assert states[0].entity_id.startswith("binary_sensor.")


async def test_overflow_on(hass: HomeAssistant, loaded_entry) -> None:
    """Payload 1 sets overflow to on."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/overflow", "1")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "on"


async def test_overflow_off(hass: HomeAssistant, loaded_entry) -> None:
    """Payload 0 sets overflow to off."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/overflow", "0")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "off"


async def test_overflow_float_payload(hass: HomeAssistant, loaded_entry) -> None:
    """Float payload 1.0 (as the device sends) is treated as on."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/overflow", "1.0")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "on"


async def test_overflow_invalid_payload(hass: HomeAssistant, loaded_entry) -> None:
    """Invalid payload leaves state as unknown."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/overflow", "bad")
    await hass.async_block_till_done()

    state = hass.states.async_all("binary_sensor")[0]
    assert state.state == "unknown"
