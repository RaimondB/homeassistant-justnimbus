"""Binary sensor platform for JustNimbus MQTT."""

from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_NAME, CONF_TOPIC_PREFIX, DOMAIN

_LOGGER = logging.getLogger(__name__)

_OVERFLOW_TOPIC_SUFFIX = "sensor/overflow"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JustNimbus MQTT binary sensors."""
    prefix = entry.data[CONF_TOPIC_PREFIX]
    device_name = entry.data[CONF_DEVICE_NAME]
    async_add_entities(
        [
            JustNimbusOverflowSensor(
                entry_id=entry.entry_id,
                device_name=device_name,
                topic_prefix=prefix,
            )
        ]
    )


class JustNimbusOverflowSensor(BinarySensorEntity):
    """Overflow binary sensor — on when the reservoir is overflowing."""

    _attr_has_entity_name = True
    _attr_translation_key = "overflow"
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_is_on: bool | None = None
    _unsubscribe: Callable[[], None] | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
    ) -> None:
        self._topic = f"{topic_prefix}/{_OVERFLOW_TOPIC_SUFFIX}"
        self._attr_unique_id = f"{entry_id}_overflow"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer="JustNimbus",
            model="Rainwater Pump",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic on add."""

        @callback
        def message_received(msg: mqtt.ReceiveMessage) -> None:
            try:
                self._attr_is_on = float(msg.payload) > 0
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid overflow payload: %r", msg.payload)
                return
            self.async_write_ha_state()

        self._unsubscribe = await mqtt.async_subscribe(
            self.hass, self._topic, message_received, qos=0
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT on remove."""
        if self._unsubscribe is not None:
            self._unsubscribe()
