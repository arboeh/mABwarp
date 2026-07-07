# custom_components/mabwarp/binary_sensor.py

from __future__ import annotations

import json
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.mqtt.client import async_subscribe
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
)
from .entity_base import MabwarpEntityBase
from .features import Feature, has_feature

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp binary sensors."""
    features = entry.data.get("features", [])
    if has_feature(features, Feature.POWER_MANAGER):
        async_add_entities([MabwarpIs3phaseBinarySensor(entry, entity_category=EntityCategory.DIAGNOSTIC)])


class MabwarpIs3phaseBinarySensor(MabwarpEntityBase, BinarySensorEntity):
    """Binary sensor for 3-phase power availability."""

    _attr_icon = "mdi:lightning-bolt"
    _attr_has_entity_name = True
    _attr_translation_key = "power_manager_is_3phase"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(entity_category=EntityCategory.DIAGNOSTIC)
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_is_on = bool(data.get("is_3phase", False))
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                self._handle_parse_error(err, self._topic)

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
        return self._build_unique_id("is_3phase")
