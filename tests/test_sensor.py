"""Tests for the JustNimbus MQTT sensor platform."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.justnimbus_mqtt.const import (
    CONF_DEVICE_NAME,
    CONF_RESERVOIR_PRESET,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PORT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    PRESET_UNKNOWN,
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
    """18 MQTT sensors plus the derived reservoir-fill sensor."""
    assert len(hass.states.async_all("sensor")) == 19


async def test_pump_starts_total(hass: HomeAssistant, loaded_entry) -> None:
    """Numeric pump-statistics topic maps to a sensor."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/stats/pump/starts/total",
        "1234",
    )
    await hass.async_block_till_done()
    state = hass.states.get(
        _entity_id(hass, loaded_entry.entry_id, "pump_starts_total")
    )
    assert state.state == "1234.0"


async def test_system_status_text(hass: HomeAssistant, loaded_entry) -> None:
    """String system topic is stored verbatim, not parsed as a number."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/system/status",
        "System Just Right!",
    )
    await hass.async_block_till_done()
    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "system_status"))
    assert state.state == "System Just Right!"


async def test_reservoir_fill_unknown_when_not_configured(
    hass: HomeAssistant,
) -> None:
    """With reservoir = Unknown, the fill sensor stays unknown."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_DEVICE_NAME,
        data={
            CONF_HOST: "192.168.1.50",
            CONF_PORT: DEFAULT_PORT,
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
        },
        options={CONF_RESERVOIR_PRESET: PRESET_UNKNOWN},
        unique_id="192.168.1.50:1883:justnimbus",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    _fire(
        hass,
        entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/volume",
        "2250",
    )
    await hass.async_block_till_done()
    state = hass.states.get(_entity_id(hass, entry.entry_id, "reservoir_fill"))
    assert state.state == "unknown"


async def test_reservoir_fill_percentage(hass: HomeAssistant, loaded_entry) -> None:
    """Fill % = reported volume / default capacity (4500 L) * 100, clamped."""
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/volume",
        "2250",
    )
    await hass.async_block_till_done()
    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "reservoir_fill"))
    assert state.state == "50.0"

    # Over capacity clamps to 100.
    _fire(
        hass,
        loaded_entry.entry_id,
        f"{DEFAULT_TOPIC_PREFIX}/sensor/water/volume",
        "9999",
    )
    await hass.async_block_till_done()
    state = hass.states.get(_entity_id(hass, loaded_entry.entry_id, "reservoir_fill"))
    assert state.state == "100.0"


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
