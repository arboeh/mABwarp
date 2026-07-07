# custom_components/mabwarp/entity_base.py

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_DEVICE_ID, CONF_WARP_VERSION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MabwarpEntityBase:
    """Mixin providing shared device_info, unique_id helper, and MQTT cleanup."""

    _parse_error_count: int = 0
    hass: HomeAssistant
    entity_id: str | None
    _config_entry: ConfigEntry
    _unsubscribe: Callable[[], Any] | None
    async_write_ha_state: Callable[[], None]

    def __init__(self, entity_category: EntityCategory | None = None) -> None:
        if entity_category is not None:
            self._attr_entity_category = entity_category

    def _build_unique_id(self, suffix: str) -> str:
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_{suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        warp_version = self._config_entry.data[CONF_WARP_VERSION]
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"WARP Charger {device_id}",
            manufacturer="Tinkerforge GmbH",
            model=warp_version,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def _schedule_state_update(self) -> None:
        """Schedule the HA state write in the event loop from any thread.

        MQTT ``on_message`` callbacks in this integration run in the paho-mqtt
        network thread, which is *not* Home Assistant's event loop. Calling
        ``async_write_ha_state`` directly from there violates HA's thread-safety
        contract and can corrupt data or crash HA. This helper reschedules the
        state write via ``call_soon_threadsafe`` so it runs on the event loop.

        Fails fast with a logged error instead of silently dropping the update
        when ``hass`` or the event loop is not (yet) available.
        """
        if self.hass is None or self.hass.loop is None:
            _LOGGER.error(
                "Cannot schedule HA state update: hass or event loop unavailable for %s",
                getattr(self, "entity_id", None),
            )
            return
        self.hass.loop.call_soon_threadsafe(self._apply_state_update)

    def _apply_state_update(self) -> None:
        """Write the entity state. Invoked from the HA event loop only."""
        self.async_write_ha_state()

    def _handle_parse_error(self, err: Exception, topic: str) -> None:
        """Increment parse error counter and mark entity unavailable after 3 consecutive failures."""
        self._parse_error_count += 1
        _LOGGER.warning("Failed to parse MQTT message on %s: %s", topic, err)
        if self._parse_error_count >= 3:
            self._attr_available = False
            self._schedule_state_update()

    def _reset_parse_error_count(self) -> None:
        """Reset parse error counter and restore availability on successful parse."""
        self._parse_error_count = 0
        self._attr_available = True
