"""Sensor platform for JustNimbus MQTT."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_NAME,
    CONF_RESERVOIR_VOLUME,
    CONF_TOPIC_PREFIX,
    DEFAULT_RESERVOIR_VOLUME,
    DOMAIN,
    signal_message,
)

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
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
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
        device_class=SensorDeviceClass.WATER,
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
        device_class=SensorDeviceClass.WATER,
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
    capacity_l = entry.options.get(CONF_RESERVOIR_VOLUME, DEFAULT_RESERVOIR_VOLUME)
    entities: list[SensorEntity] = [
        JustNimbusMqttSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
            description=desc,
        )
        for desc in SENSOR_DESCRIPTIONS
    ]
    entities.append(
        JustNimbusReservoirFillSensor(
            entry_id=entry.entry_id,
            device_name=device_name,
            topic_prefix=prefix,
            capacity_l=capacity_l,
        )
    )
    async_add_entities(entities)


class JustNimbusMqttSensor(SensorEntity):
    """A JustNimbus sensor updated via the integration's MQTT dispatcher."""

    _attr_has_entity_name = True
    _attr_native_value: float | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
        description: JustNimbusSensorDescription,
    ) -> None:
        self.entity_description: JustNimbusSensorDescription = description
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
            try:
                self._attr_native_value = float(payload)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid payload on %s: %r", self._topic, payload)
                return
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_message(self._entry_id),
                _message_received,
            )
        )


class JustNimbusReservoirFillSensor(SensorEntity):
    """Reservoir fill level (%), derived from reported volume vs capacity."""

    _attr_has_entity_name = True
    _attr_translation_key = "reservoir_fill"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_native_value: float | None = None

    def __init__(
        self,
        *,
        entry_id: str,
        device_name: str,
        topic_prefix: str,
        capacity_l: int,
    ) -> None:
        self._entry_id = entry_id
        self._topic = f"{topic_prefix}/sensor/water/volume"
        self._capacity_l = capacity_l
        self._attr_unique_id = f"{entry_id}_reservoir_fill"
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
                volume_l = float(payload)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid payload on %s: %r", self._topic, payload)
                return
            pct = volume_l / self._capacity_l * 100 if self._capacity_l else 0.0
            self._attr_native_value = round(min(100.0, max(0.0, pct)), 1)
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_message(self._entry_id),
                _message_received,
            )
        )
