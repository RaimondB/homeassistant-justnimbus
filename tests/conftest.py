"""Shared test fixtures."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"

from custom_components.justnimbus_mqtt.const import (  # noqa: E402
    CONF_DEVICE_NAME,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PORT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)

_TEST_HOST = "192.168.1.100"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Allow any internal timers to outlive individual tests."""
    return True


class _BlockingMessages:
    """Async iterator that blocks forever — simulates waiting for MQTT messages."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        # Block until the background task is cancelled by hass shutdown
        await asyncio.get_event_loop().create_future()
        raise StopAsyncIteration


class _FakeMqttClient:
    """MQTT client stub that connects but never delivers messages."""

    def __init__(self, *args, **kwargs):
        self.messages = _BlockingMessages()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def subscribe(self, *args, **kwargs):
        pass


@pytest.fixture
def config_entry(hass):
    """A minimal config entry wired to the test hass instance."""
    from homeassistant.const import CONF_HOST, CONF_PORT

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_DEVICE_NAME,
        data={
            CONF_HOST: _TEST_HOST,
            CONF_PORT: DEFAULT_PORT,
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
        },
        unique_id=f"{_TEST_HOST}:{DEFAULT_PORT}:{DEFAULT_TOPIC_PREFIX}",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def loaded_entry(hass, config_entry):
    """Load the integration with a stubbed MQTT client."""
    with patch("custom_components.justnimbus_mqtt.aiomqtt.Client", _FakeMqttClient):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry
