"""Shared test fixtures."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"

from custom_components.justnimbus_mqtt.const import (  # noqa: E402
    CONF_DEVICE_NAME,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Allow MQTT client's periodic timer to outlive the test."""
    return True


@pytest.fixture
def config_entry(hass):
    """A minimal config entry wired to the test hass instance."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_DEVICE_NAME,
        data={
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
        },
        unique_id=DEFAULT_TOPIC_PREFIX,
    )
    entry.add_to_hass(hass)
    return entry
