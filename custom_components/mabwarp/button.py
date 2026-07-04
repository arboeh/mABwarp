# custom_components/mabwarp/button.py

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.components.mqtt.client import async_publish
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DOMAIN,
    TOPIC_CHARGE_LIMITS_RESTART,
    TOPIC_EVSE_START,
    TOPIC_EVSE_STOP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp buttons."""
    topic_prefix = entry.data[CONF_TOPIC_PREFIX]
    features = entry.data.get("features", [])

    entities = [
        MabwarpButtonBase(
            entry,
            "Start Charging",
            TOPIC_EVSE_START.format(prefix=topic_prefix),
            "mdi:play-circle",
        ),
        MabwarpButtonBase(
            entry,
            "Stop Charging",
            TOPIC_EVSE_STOP.format(prefix=topic_prefix),
            "mdi:stop-circle",
        ),
    ]

    if "charge_limits" in features:
        entities.append(
            MabwarpButtonBase(
                entry,
                "Restart Charge Limits",
                TOPIC_CHARGE_LIMITS_RESTART.format(prefix=topic_prefix),
                "mdi:restart",
            )
        )

    async_add_entities(entities)


class MabwarpButtonBase(ButtonEntity):
    """Base class for mABwarp MQTT buttons."""

    def __init__(self, config_entry: ConfigEntry, name: str, topic: str, icon: str) -> None:
        """Initialize the button."""
        self._config_entry = config_entry
        self._topic = topic
        self._attr_name = name
        self._attr_icon = icon

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.info("Button pressed: %s", self._topic)
        await async_publish(
            self.hass,
            self._topic,
            None,
            qos=0,
            retain=False,
            encoding=None,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this button."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        safe_topic = self._topic.replace("/", "_")
        return f"{DOMAIN}_{device_id}_{safe_topic}"

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
