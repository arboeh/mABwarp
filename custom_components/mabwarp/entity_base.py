# custom_components/mabwarp/entity_base.py

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_DEVICE_ID, CONF_WARP_VERSION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MabwarpEntityBase:
    """Mixin providing shared device_info, unique_id helper, and MQTT cleanup."""

    _parse_error_count: int = 0

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
        if getattr(self, "_unsubscribe", None):
            self._unsubscribe()
            self._unsubscribe = None

    def _handle_parse_error(self, err: Exception, topic: str) -> None:
        """Increment parse error counter and mark entity unavailable after 3 consecutive failures."""
        self._parse_error_count += 1
        _LOGGER.warning("Failed to parse MQTT message on %s: %s", topic, err)
        if self._parse_error_count >= 3:
            self._attr_available = False
            self.async_write_ha_state()

    def _reset_parse_error_count(self) -> None:
        """Reset parse error counter and restore availability on successful parse."""
        self._parse_error_count = 0
        if not self._attr_available:
            self._attr_available = True
            self.async_write_ha_state()
