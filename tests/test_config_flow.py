"""Tests for the JustNimbus MQTT config flow."""

from __future__ import annotations

import voluptuous_serialize
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv

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
    PRESET_UNKNOWN,
    RESERVOIR_PRESETS,
)

_HOST = "192.168.1.100"

_VALID_INPUT = {
    CONF_HOST: _HOST,
    CONF_PORT: DEFAULT_PORT,
    CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
    CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
}

# All four dimension keys are required by the schema even for Unknown
# (resolve ignores them); supply placeholders.
_RESERVOIR_UNKNOWN = {
    CONF_RESERVOIR_PRESET: PRESET_UNKNOWN,
    CONF_RESERVOIR_LENGTH: 1,
    CONF_RESERVOIR_WIDTH: 1,
    CONF_RESERVOIR_HEIGHT: 1,
    CONF_RESERVOIR_VOLUME: 1,
}


async def _add_device(hass: HomeAssistant, conn: dict, reservoir: dict):
    """Drive the two-step add flow: connection -> reservoir."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=conn
    )
    if result["type"] != FlowResultType.FORM:
        return result  # e.g. aborted at the connection step
    assert result["step_id"] == "reservoir"
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=reservoir
    )


async def test_form_shows(hass: HomeAssistant) -> None:
    """Config flow shows the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_create_entry_unknown_reservoir(hass: HomeAssistant) -> None:
    """Full add flow with Unknown reservoir creates the entry."""
    result = await _add_device(hass, _VALID_INPUT, _RESERVOIR_UNKNOWN)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_DEVICE_NAME
    assert result["data"][CONF_HOST] == _HOST
    assert result["options"][CONF_RESERVOIR_PRESET] == PRESET_UNKNOWN
    # Unknown stores no dimensions.
    assert CONF_RESERVOIR_VOLUME not in result["options"]


async def test_create_entry_preset_reservoir(hass: HomeAssistant) -> None:
    """Add flow with a standard preset stores that preset's dimensions."""
    reservoir = {**_RESERVOIR_UNKNOWN, CONF_RESERVOIR_PRESET: "standard_4500"}
    result = await _add_device(hass, _VALID_INPUT, reservoir)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    expected = RESERVOIR_PRESETS["standard_4500"]
    assert result["options"][CONF_RESERVOIR_VOLUME] == expected[CONF_RESERVOIR_VOLUME]


async def test_duplicate_aborts(hass: HomeAssistant) -> None:
    """Second flow with the same host:port:prefix is aborted."""
    first = await _add_device(hass, _VALID_INPUT, _RESERVOIR_UNKNOWN)
    assert first["type"] == FlowResultType.CREATE_ENTRY

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=_VALID_INPUT
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_different_host_allowed(hass: HomeAssistant) -> None:
    """Two entries with different hosts can coexist."""
    first = await _add_device(hass, _VALID_INPUT, _RESERVOIR_UNKNOWN)
    assert first["type"] == FlowResultType.CREATE_ENTRY

    second = await _add_device(
        hass, {**_VALID_INPUT, CONF_HOST: "192.168.1.200"}, _RESERVOIR_UNKNOWN
    )
    assert second["type"] == FlowResultType.CREATE_ENTRY


async def test_options_schema_is_frontend_serializable(
    hass: HomeAssistant, loaded_entry
) -> None:
    """The options form schema must serialize like the HA frontend does.

    Regression: a bare callable schema type validates fine in tests but
    voluptuous_serialize (used to render the form) raises on it, so the
    real UI failed with "config flow could not be loaded" while every
    pytest stayed green. Replicate that serialization here.
    """
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    serialized = voluptuous_serialize.convert(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    # Every field must serialize to a dict (no opaque callables left).
    assert all(isinstance(field, dict) for field in serialized)


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


async def test_options_flow_unknown(hass: HomeAssistant, loaded_entry) -> None:
    """Selecting Unknown clears the reservoir dimensions."""
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_RESERVOIR_PRESET: PRESET_UNKNOWN,
            CONF_RESERVOIR_LENGTH: 1,
            CONF_RESERVOIR_WIDTH: 1,
            CONF_RESERVOIR_HEIGHT: 1,
            CONF_RESERVOIR_VOLUME: 1,
        },
    )
    await hass.async_block_till_done()
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert loaded_entry.options[CONF_RESERVOIR_PRESET] == PRESET_UNKNOWN
    assert CONF_RESERVOIR_VOLUME not in loaded_entry.options


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
