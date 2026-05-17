"""JustNimbus MQTT integration."""

from __future__ import annotations

import asyncio
import logging

import aiomqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_TOPIC_PREFIX,
    DATA_MQTT_TASK,
    DOMAIN,
    PLATFORMS,
    signal_message,
)

_LOGGER = logging.getLogger(__name__)

_RECONNECT_DELAY = 5


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JustNimbus MQTT from a config entry."""
    host: str = entry.data[CONF_HOST]
    port: int = entry.data[CONF_PORT]
    prefix: str = entry.data[CONF_TOPIC_PREFIX]

    async def _mqtt_loop() -> None:
        while True:
            try:
                async with aiomqtt.Client(hostname=host, port=port) as client:
                    _LOGGER.debug(
                        "Connected to JustNimbus MQTT broker at %s:%s", host, port
                    )
                    await client.subscribe(f"{prefix}/#")
                    async for msg in client.messages:
                        async_dispatcher_send(
                            hass,
                            signal_message(entry.entry_id),
                            str(msg.topic),
                            msg.payload.decode(),
                        )
            except aiomqtt.MqttError as err:
                _LOGGER.warning(
                    "JustNimbus MQTT connection to %s:%s lost (%s); retrying in %ss",
                    host,
                    port,
                    err,
                    _RECONNECT_DELAY,
                )
                await asyncio.sleep(_RECONNECT_DELAY)
            except asyncio.CancelledError:
                raise

    task = hass.async_create_background_task(
        _mqtt_loop(), f"{DOMAIN}_mqtt_{entry.entry_id}"
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_MQTT_TASK: task}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    task: asyncio.Task = hass.data[DOMAIN][entry.entry_id][DATA_MQTT_TASK]
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
