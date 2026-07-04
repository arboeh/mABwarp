# custom_components/mabwarp/binary_sensor.py

from __future__ import annotations

import json
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.mqtt.client import async_subscribe
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DOMAIN,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp binary sensors."""
    features = entry.data.get("features", [])
    if "power_manager" in features:
        async_add_entities([MabwarpIs3phaseBinarySensor(entry)])


class MabwarpIs3phaseBinarySensor(BinarySensorEntity):
    """Binary sensor for 3-phase power availability."""

    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_is_on = bool(data.get("is_3phase", False))
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        self._topic = TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=topic_prefix)
        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this binary sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_is_3phase"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        warp_version = self._config_entry.data[CONF_WARP_VERSION]
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"WARP Charger {device_id}",
            manufacturer="Tinkerforge GmbH",
            model=warp_version,
        )
