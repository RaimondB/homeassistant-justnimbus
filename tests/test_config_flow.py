"""Tests for the JustNimbus MQTT config flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.justnimbus_mqtt.const import (
    CONF_DEVICE_NAME,
    CONF_RESERVOIR_PRESET,
    CONF_RESERVOIR_VOLUME,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PORT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
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


async def test_options_flow_preset_prefill(hass: HomeAssistant, loaded_entry) -> None:
    """Picking a standard preset prefills and saves the dimensions."""
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_RESERVOIR_PRESET: "standard_4500"},
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "dimensions"

    expected = RESERVOIR_PRESETS["standard_4500"]
    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"], user_input=dict(expected)
    )
    await hass.async_block_till_done()
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert (
        loaded_entry.options[CONF_RESERVOIR_VOLUME] == expected[CONF_RESERVOIR_VOLUME]
    )
