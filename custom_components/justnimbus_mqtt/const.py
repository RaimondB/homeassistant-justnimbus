"""Constants for the JustNimbus MQTT integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "justnimbus_mqtt"

PLATFORMS: Final[list[Platform]] = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONF_TOPIC_PREFIX: Final = "topic_prefix"
CONF_DEVICE_NAME: Final = "device_name"

# Physical reservoir ("zak") dimensions, configured via the options flow.
CONF_RESERVOIR_LENGTH: Final = "reservoir_length_mm"
CONF_RESERVOIR_WIDTH: Final = "reservoir_width_mm"
CONF_RESERVOIR_HEIGHT: Final = "reservoir_height_mm"
CONF_RESERVOIR_VOLUME: Final = "reservoir_volume_l"

DEFAULT_TOPIC_PREFIX: Final = "justnimbus"
DEFAULT_DEVICE_NAME: Final = "JustNimbus"
DEFAULT_PORT: Final = 1883

DEFAULT_RESERVOIR_LENGTH: Final = 3600
DEFAULT_RESERVOIR_WIDTH: Final = 2500
DEFAULT_RESERVOIR_HEIGHT: Final = 500
DEFAULT_RESERVOIR_VOLUME: Final = 4500

CONF_RESERVOIR_PRESET: Final = "reservoir_preset"
PRESET_CUSTOM: Final = "custom"
# No reservoir configured: the derived fill/full entities stay "unknown".
PRESET_UNKNOWN: Final = "unknown"

# The two standard residential rainwater bags ("zak"). Dimensions are the
# typical footprint; the litre figure is the rated capacity (the bag is not
# a perfect box, so volume drives the fill %, not L*W*H).
RESERVOIR_PRESETS: Final[dict[str, dict[str, int]]] = {
    "standard_3000": {
        CONF_RESERVOIR_LENGTH: 2600,
        CONF_RESERVOIR_WIDTH: 2600,
        CONF_RESERVOIR_HEIGHT: 500,
        CONF_RESERVOIR_VOLUME: 3000,
    },
    "standard_4500": {
        CONF_RESERVOIR_LENGTH: 3500,
        CONF_RESERVOIR_WIDTH: 2600,
        CONF_RESERVOIR_HEIGHT: 500,
        CONF_RESERVOIR_VOLUME: 4500,
    },
}

DATA_MQTT_TASK: Final = "mqtt_task"


def signal_message(entry_id: str) -> str:
    """Return the dispatcher signal key for MQTT messages from this entry."""
    return f"{DOMAIN}_{entry_id}_message"
