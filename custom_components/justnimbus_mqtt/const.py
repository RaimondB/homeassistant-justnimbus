"""Constants for the JustNimbus MQTT integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "justnimbus_mqtt"

PLATFORMS: Final[list[Platform]] = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONF_TOPIC_PREFIX: Final = "topic_prefix"
CONF_DEVICE_NAME: Final = "device_name"

DEFAULT_TOPIC_PREFIX: Final = "justnimbus"
DEFAULT_DEVICE_NAME: Final = "JustNimbus"
