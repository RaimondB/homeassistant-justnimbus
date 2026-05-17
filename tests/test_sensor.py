"""Tests for the JustNimbus MQTT sensor platform."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_mqtt_message


def _entity_id(
    hass: HomeAssistant, entry_id: str, key: str, domain: str = "sensor"
) -> str:
    """Look up entity_id by unique_id."""
    registry = er.async_get(hass)
    unique_id = f"{entry_id}_{key}"
    entity_id = registry.async_get_entity_id(domain, "justnimbus_mqtt", unique_id)
    assert entity_id is not None, f"Entity '{key}' not found"
    return entity_id


@pytest.fixture
async def loaded_entry(hass: HomeAssistant, config_entry, mqtt_mock):
    """Set up the integration and wait for entities to register."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_sensor_count(hass: HomeAssistant, loaded_entry) -> None:
    """Twelve sensor entities should be created."""
    states = hass.states.async_all("sensor")
    assert len(states) == 12


async def test_pump_pressure_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Sensor state updates when an MQTT message arrives."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/water/pressure", "1.8")
    await hass.async_block_till_done()

    state = next(
        s for s in hass.states.async_all("sensor") if "pressure" in s.entity_id
    )
    assert state.state == "1.8"


async def test_reservoir_temp_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Reservoir temperature sensor updates correctly."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/water/temp", "14.5")
    await hass.async_block_till_done()

    state = next(s for s in hass.states.async_all("sensor") if "temp" in s.entity_id)
    assert state.state == "14.5"


async def test_waterflow_in_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Water flow in sensor updates correctly."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/waterflow/in", "3.2")
    await hass.async_block_till_done()

    entity_id = _entity_id(hass, loaded_entry.entry_id, "waterflow_in")
    assert hass.states.get(entity_id).state == "3.2"


async def test_water_used_total_updates(hass: HomeAssistant, loaded_entry) -> None:
    """Total water used statistic updates correctly."""
    async_fire_mqtt_message(hass, "justnimbus/stats/water/used/total", "12345.0")
    await hass.async_block_till_done()

    entity_id = _entity_id(hass, loaded_entry.entry_id, "water_used_total")
    assert hass.states.get(entity_id).state == "12345.0"


async def test_invalid_payload_ignored(hass: HomeAssistant, loaded_entry) -> None:
    """Non-numeric payload leaves state as unknown rather than crashing."""
    async_fire_mqtt_message(hass, "justnimbus/sensor/water/pressure", "bad")
    await hass.async_block_till_done()

    state = next(
        s for s in hass.states.async_all("sensor") if "pressure" in s.entity_id
    )
    assert state.state == "unknown"


async def test_custom_topic_prefix(hass: HomeAssistant, mqtt_mock) -> None:
    """Entities subscribe under the configured prefix, not the default."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.justnimbus_mqtt.const import (
        CONF_DEVICE_NAME,
        CONF_TOPIC_PREFIX,
        DOMAIN,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="My Pump",
        data={CONF_TOPIC_PREFIX: "mypump", CONF_DEVICE_NAME: "My Pump"},
        unique_id="mypump",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "mypump/sensor/water/pressure", "2.1")
    await hass.async_block_till_done()

    state = next(
        s for s in hass.states.async_all("sensor") if "pressure" in s.entity_id
    )
    assert state.state == "2.1"
