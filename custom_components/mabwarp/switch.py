# custom_components/mabwarp/switch.py

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DOMAIN,
    TOPIC_EVSE_SET_USER_ENABLED,
    TOPIC_EVSE_USER_ENABLED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp switches."""
    async_add_entities([MabwarpUserEnabledSwitch(entry)])


class MabwarpUserEnabledSwitch(SwitchEntity):
    """Switch to enable or disable the WARP Charger."""

    _attr_name = "Wallbox Enabled"
    _attr_icon = "mdi:ev-station"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the switch."""
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_is_on = False

        prefix = config_entry.data[CONF_TOPIC_PREFIX]
        self._subscribe_topic = TOPIC_EVSE_USER_ENABLED.format(prefix=prefix)
        self._set_topic = TOPIC_EVSE_SET_USER_ENABLED.format(prefix=prefix)

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_is_on = data["enabled"]
                self.async_write_ha_state()
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._subscribe_topic, err)

        self._unsubscribe = await self.hass.components.mqtt.async_subscribe(self._subscribe_topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    async def _async_publish_enabled(self, enabled: bool) -> None:
        """Publish enabled state to MQTT."""
        payload = json.dumps({"enabled": enabled})
        await self.hass.components.mqtt.async_publish(
            self.hass,
            self._set_topic,
            payload,
            qos=0,
            retain=False,
            encoding="utf-8",
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_publish_enabled(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_publish_enabled(False)
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        """Return unique ID for this switch."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_user_enabled"

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
