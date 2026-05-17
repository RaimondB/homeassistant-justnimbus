"""Tests for the JustNimbus MQTT config flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.justnimbus_mqtt.const import (
    CONF_DEVICE_NAME,
    CONF_RESERVOIR_HEIGHT,
    CONF_RESERVOIR_LENGTH,
    CONF_RESERVOIR_PRESET,
    CONF_RESERVOIR_VOLUME,
    CONF_RESERVOIR_WIDTH,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PORT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    PRESET_CUSTOM,
    RESERVOIR_PRESETS,
)

_HOST = "192.168.1.100"

_VALID_INPUT = {
    CONF_HOST: _HOST,
    CONF_PORT: DEFAULT_PORT,
    CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
    CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
}


async def test_form_shows(hass: HomeAssistant) -> None:
    """Config flow shows the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_create_entry(hass: HomeAssistant) -> None:
    """Submitting valid data creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=_VALID_INPUT
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == DEFAULT_DEVICE_NAME
    assert result2["data"][CONF_HOST] == _HOST
    assert result2["data"][CONF_PORT] == DEFAULT_PORT
    assert result2["data"][CONF_TOPIC_PREFIX] == DEFAULT_TOPIC_PREFIX


async def test_duplicate_aborts(hass: HomeAssistant) -> None:
    """Second flow with the same host:port:prefix is aborted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=_VALID_INPUT
    )

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], user_input=_VALID_INPUT
    )
    assert result3["type"] == FlowResultType.ABORT
    assert result3["reason"] == "already_configured"


async def test_different_host_allowed(hass: HomeAssistant) -> None:
    """Two entries with different hosts can coexist."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=_VALID_INPUT
    )

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={**_VALID_INPUT, CONF_HOST: "192.168.1.200"},
    )
    assert result3["type"] == FlowResultType.CREATE_ENTRY


async def test_options_flow_preset(hass: HomeAssistant, loaded_entry) -> None:
    """A standard preset saves its own dimensions in one step."""
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    expected = RESERVOIR_PRESETS["standard_4500"]
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RESERVOIR_PRESET: "standard_4500",
            # Boxes are ignored when a standard preset is chosen.
            CONF_RESERVOIR_LENGTH: 1,
            CONF_RESERVOIR_WIDTH: 1,
            CONF_RESERVOIR_HEIGHT: 1,
            CONF_RESERVOIR_VOLUME: 1,
        },
    )
    await hass.async_block_till_done()
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    opts = loaded_entry.options
    assert opts[CONF_RESERVOIR_VOLUME] == expected[CONF_RESERVOIR_VOLUME]
    assert opts[CONF_RESERVOIR_LENGTH] == expected[CONF_RESERVOIR_LENGTH]


async def test_options_flow_custom(hass: HomeAssistant, loaded_entry) -> None:
    """Custom uses the values entered in the boxes."""
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RESERVOIR_PRESET: PRESET_CUSTOM,
            CONF_RESERVOIR_LENGTH: 4000,
            CONF_RESERVOIR_WIDTH: 3000,
            CONF_RESERVOIR_HEIGHT: 600,
            CONF_RESERVOIR_VOLUME: 7000,
        },
    )
    await hass.async_block_till_done()
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert loaded_entry.options[CONF_RESERVOIR_VOLUME] == 7000
    assert loaded_entry.options[CONF_RESERVOIR_HEIGHT] == 600
