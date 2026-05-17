"""Sensor platform for JustNimbus MQTT."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components import mqtt
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_NAME, CONF_TOPIC_PREFIX, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class JustNimbusSensorDescription(SensorEntityDescription):
    """Describes a JustNimbus MQTT sensor."""

    topic_suffix: str


SENSOR_DESCRIPTIONS: tuple[JustNimbusSensorDescription, ...] = (
    JustNimbusSensorDescription(
        key="pump_pressure",
        translation_key="pump_pressure",
        topic_suffix="sensor/water/pressure",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    JustNimbusSensorDescription(
        key="reservoir_temp",
        translation_key="reservoir_temp",
        topic_suffix="sensor/water/temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    JustNimbusSensorDescription(
        key="water_volume",
        translation_key="water_volume",
        topic_suffix="sensor/water/volume",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    JustNimbusSensorDescription(
        key="water_height",
        translation_key="water_height",
        topic_suffix="sensor/water/height",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    JustNimbusSensorDescription(
        key="waterflow_in",
        translation_key="waterflow_in",
        topic_suffix="sensor/waterflow/in",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    JustNimbusSensorDescription(
        key="waterflow_out",
        translation_key="waterflow_out",
        topic_suffix="sensor/waterflow/out",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    JustNimbusSensorDescription(
        key="water_used_hour",
        translation_key="water_used_hour",
        topic_suffix="stats/water/used/hour",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    JustNimbusSensorDescription(
        key="water_used_24h",
        translation_key="water_used_24h",
        topic_suffix="stats/water/used/24h",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    JustNimbusSensorDescription(
        key="water_used_total",
        translation_key="water_used_total",
        topic_suffix="stats/water/used/total",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    JustNimbusSensorDescription(
        key="water_added_hour",
        translation_key="water_added_hour",
        topic_suffix="stats/water/added/hour",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    JustNimbusSensorDescription(
        key="water_added_24h",
        translation_key="water_added_24h",
        topic_suffix="stats/water/added/24h",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    JustNimbusSensorDescription(
        key="water_added_total",
        translation_key="water_added_total",
        topic_suffix="stats/water/added/total",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JustNimbus MQTT sensors."""
    prefix = entry.data[CONF_TOPIC_PREFIX]
    device_name = entry.data[CONF_DEVICE_NAME]
    async_add_entities(
        JustNimbusMqttSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
            description=desc,
        )
        for desc in SENSOR_DESCRIPTIONS
    )


class JustNimbusMqttSensor(SensorEntity):
    """A JustNimbus sensor reading from an MQTT topic."""

    _attr_has_entity_name = True
    _attr_native_value: float | None = None
    _unsubscribe: Callable[[], None] | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
        description: JustNimbusSensorDescription,
    ) -> None:
        self.entity_description: JustNimbusSensorDescription = description
        self._topic = f"{topic_prefix}/{description.topic_suffix}"
        self._attr_unique_id = f"{entry_id}_{description.key}"
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
                self._attr_native_value = float(msg.payload)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid payload on %s: %r", self._topic, msg.payload)
                return
            self.async_write_ha_state()

        self._unsubscribe = await mqtt.async_subscribe(
            self.hass, self._topic, message_received, qos=0
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT on remove."""
        if self._unsubscribe is not None:
            self._unsubscribe()
