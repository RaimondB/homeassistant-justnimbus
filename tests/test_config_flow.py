"""Tests for the JustNimbus MQTT config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.justnimbus_mqtt.const import (
    CONF_DEVICE_NAME,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def _mqtt_available(hass):
    """Simulate MQTT client being available."""
    with patch(
        "homeassistant.components.mqtt.async_wait_for_mqtt_client",
        return_value=True,
    ):
        yield


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
        result["flow_id"],
        user_input={
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == DEFAULT_DEVICE_NAME
    assert result2["data"][CONF_TOPIC_PREFIX] == DEFAULT_TOPIC_PREFIX


async def test_duplicate_aborts(hass: HomeAssistant) -> None:
    """Second flow with the same topic prefix is aborted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
        },
    )

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
        },
    )
    assert result3["type"] == FlowResultType.ABORT
    assert result3["reason"] == "already_configured"


async def test_mqtt_not_configured_aborts(hass: HomeAssistant) -> None:
    """Flow aborts when MQTT integration is not configured."""
    with patch(
        "homeassistant.components.mqtt.async_wait_for_mqtt_client",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "mqtt_not_configured"
