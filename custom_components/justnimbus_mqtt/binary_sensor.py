"""Binary sensor platform for JustNimbus MQTT."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_NAME,
    CONF_RESERVOIR_HEIGHT,
    CONF_TOPIC_PREFIX,
    DOMAIN,
    signal_message,
)

_LOGGER = logging.getLogger(__name__)

_OVERFLOW_TOPIC_SUFFIX = "sensor/overflow"
_HEIGHT_TOPIC_SUFFIX = "sensor/water/height"
_ERROR_TOPIC_SUFFIX = "system/error"


@dataclass(frozen=True, kw_only=True)
class JustNimbusActuatorDescription(BinarySensorEntityDescription):
    """An actuator topic whose payload looks like 'valvein.off'."""

    topic_suffix: str


# Payload is "<name>.<state>" — on when the trailing token is "on".
ACTUATOR_DESCRIPTIONS: tuple[JustNimbusActuatorDescription, ...] = (
    JustNimbusActuatorDescription(
        key="pump_actuator",
        translation_key="pump_actuator",
        topic_suffix="actuator/pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=None,
    ),
    JustNimbusActuatorDescription(
        key="valve_in_actuator",
        translation_key="valve_in_actuator",
        topic_suffix="actuator/valve/in",
        device_class=BinarySensorDeviceClass.OPENING,
        entity_category=None,
    ),
    JustNimbusActuatorDescription(
        key="valve_out_actuator",
        translation_key="valve_out_actuator",
        topic_suffix="actuator/valve/out",
        device_class=BinarySensorDeviceClass.OPENING,
        entity_category=None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JustNimbus MQTT binary sensors."""
    prefix = entry.data[CONF_TOPIC_PREFIX]
    device_name = entry.data[CONF_DEVICE_NAME]
    # No default: an unconfigured / "unknown" reservoir has no height, so
    # the full sensor stays unknown rather than guessing.
    reservoir_height_mm = entry.options.get(CONF_RESERVOIR_HEIGHT)
    entities: list[BinarySensorEntity] = [
        JustNimbusOverflowSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
        ),
        JustNimbusReservoirFullSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
            reservoir_height_mm=reservoir_height_mm,
        ),
        JustNimbusSystemErrorSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
        ),
    ]
    entities.extend(
        JustNimbusActuatorSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
            description=desc,
        )
        for desc in ACTUATOR_DESCRIPTIONS
    )
    async_add_entities(entities)


class JustNimbusOverflowSensor(BinarySensorEntity):
    """Overflow binary sensor — on when the reservoir is overflowing."""

    _attr_has_entity_name = True
    _attr_translation_key = "overflow"
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_is_on: bool | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
    ) -> None:
        self._entry_id = entry_id
        self._topic = f"{topic_prefix}/{_OVERFLOW_TOPIC_SUFFIX}"
        self._attr_unique_id = f"{entry_id}_overflow"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer="JustNimbus",
            model="Rainwater Pump",
        )

    async def async_added_to_hass(self) -> None:
        """Register dispatcher listener."""

        @callback
        def _message_received(topic: str, payload: str) -> None:
            if topic != self._topic:
                return
            try:
                self._attr_is_on = float(payload) > 0
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid overflow payload: %r", payload)
                return
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_message(self._entry_id),
                _message_received,
            )
        )


class JustNimbusSystemErrorSensor(BinarySensorEntity):
    """Problem sensor — on when the device reports a non-zero error code."""

    _attr_has_entity_name = True
    _attr_translation_key = "system_error"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = None
    _attr_is_on: bool | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
    ) -> None:
        self._entry_id = entry_id
        self._topic = f"{topic_prefix}/{_ERROR_TOPIC_SUFFIX}"
        self._attr_unique_id = f"{entry_id}_system_error"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer="JustNimbus",
            model="Rainwater Pump",
        )

    async def async_added_to_hass(self) -> None:
        """Register dispatcher listener."""

        @callback
        def _message_received(topic: str, payload: str) -> None:
            if topic != self._topic:
                return
            try:
                self._attr_is_on = float(payload) != 0
            except (ValueError, TypeError):
                # Non-numeric error string is itself a problem.
                self._attr_is_on = payload.strip() not in ("", "0")
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_message(self._entry_id),
                _message_received,
            )
        )


class JustNimbusActuatorSensor(BinarySensorEntity):
    """Actuator state from a '<name>.on' / '<name>.off' payload."""

    _attr_has_entity_name = True
    _attr_is_on: bool | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
        description: JustNimbusActuatorDescription,
    ) -> None:
        self.entity_description = description
        self._entry_id = entry_id
        self._topic = f"{topic_prefix}/{description.topic_suffix}"
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer="JustNimbus",
            model="Rainwater Pump",
        )

    async def async_added_to_hass(self) -> None:
        """Register dispatcher listener."""

        @callback
        def _message_received(topic: str, payload: str) -> None:
            if topic != self._topic:
                return
            tail = payload.strip().rsplit(".", 1)[-1].lower()
            if tail == "on":
                self._attr_is_on = True
            elif tail == "off":
                self._attr_is_on = False
            else:
                _LOGGER.warning(
                    "Unexpected actuator payload on %s: %r", self._topic, payload
                )
                return
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_message(self._entry_id),
                _message_received,
            )
        )


class JustNimbusReservoirFullSensor(BinarySensorEntity):
    """On when the water height reaches the configured reservoir height."""

    _attr_has_entity_name = True
    _attr_translation_key = "reservoir_full"
    _attr_is_on: bool | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
        reservoir_height_mm: int | None,
    ) -> None:
        self._entry_id = entry_id
        self._topic = f"{topic_prefix}/{_HEIGHT_TOPIC_SUFFIX}"
        self._reservoir_height_mm = reservoir_height_mm
        self._attr_unique_id = f"{entry_id}_reservoir_full"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer="JustNimbus",
            model="Rainwater Pump",
        )

    async def async_added_to_hass(self) -> None:
        """Register dispatcher listener."""

        # No reservoir height configured ("unknown"): stay unknown.
        if not self._reservoir_height_mm:
            return

        @callback
        def _message_received(topic: str, payload: str) -> None:
            if topic != self._topic:
                return
            try:
                height_mm = float(payload)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid height payload: %r", payload)
                return
            self._attr_is_on = height_mm >= self._reservoir_height_mm
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_message(self._entry_id),
                _message_received,
            )
        )
