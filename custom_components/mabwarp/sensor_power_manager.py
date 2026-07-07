# custom_components/mabwarp/sensor_power_manager.py

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CHARGE_MODE_MAP,
    CONF_TOPIC_PREFIX,
    CONFIG_ERROR_FLAG_BITS,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
    TOPIC_POWER_MANAGER_STATE,
)
from .entity_base import MabwarpEntityBase
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpChargeModeSensor(MabwarpEntityBase, SensorEntity):
    """Sensor for WARP Power Manager charge mode with text mapping.

    WARNING: The text mapping is based on an unverified assumption about
    the WARP web UI and may not exactly match the charger firmware or
    official documentation. See const.py CHARGE_MODE_MAP for details.
    """

    _attr_icon = "mdi:ev-station"
    _attr_native_value = None
    _attr_has_entity_name = True
    _attr_translation_key = "power_manager_charge_mode"

    def __init__(
        self, config_entry: ConfigEntry, topic_prefix: str, entity_category: EntityCategory | None = None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entity_category=entity_category)
        self._config_entry = config_entry
        self._topic = TOPIC_POWER_MANAGER_CHARGE_MODE.format(prefix=topic_prefix)
        self._unsubscribe = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                mode = data.get("mode")
                if mode is not None:
                    self._attr_native_value = CHARGE_MODE_MAP.get(int(mode), f"Unknown ({mode})")
                    self._attr_extra_state_attributes = {"mode": int(mode)}
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                self._handle_parse_error(err, self._topic)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        return self._build_unique_id(f"{self._topic.replace('/', '_')}_charge_mode")


class MabwarpConfigErrorFlagsSensor(MabwarpEntityBase, SensorEntity):
    """Sensor for WARP Power Manager config error flags with bit decoding."""

    _attr_icon = "mdi:alert-circle"
    _attr_native_value = None
    _attr_has_entity_name = True
    _attr_translation_key = "power_manager_config_error_flags"

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(entity_category=EntityCategory.DIAGNOSTIC)
        self._config_entry = config_entry
        self._topic = TOPIC_POWER_MANAGER_STATE.format(prefix=topic_prefix)
        self._unsubscribe = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                flags = data.get("config_error_flags")
                if flags is not None:
                    self._attr_native_value = int(flags)
                    decoded: dict[str, bool] = {}
                    for idx, flag_name in enumerate(CONFIG_ERROR_FLAG_BITS):
                        decoded[flag_name] = bool(int(flags) & (1 << idx))
                    self._attr_extra_state_attributes = decoded
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                self._handle_parse_error(err, self._topic)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        return self._build_unique_id(f"{self._topic.replace('/', '_')}_config_error_flags")


def build_power_manager_entities(entry, topic_prefix: str, features: list) -> list:
    """Build power manager sensor entities."""
    has_power_manager = "power_manager" in features
    if not has_power_manager:
        return []

    entities = [
        MabwarpChargeModeSensor(entry, topic_prefix),
        MabwarpMqttSensor(
            entry,
            TOPIC_POWER_MANAGER_STATE.format(prefix=topic_prefix),
            "Power Manager Config Error Flags",
            "config_error_flags",
            None,
            None,
            None,
            coordinator=None,
            translation_key="power_manager_config_error_flags",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        MabwarpMqttSensor(
            entry,
            TOPIC_POWER_MANAGER_STATE.format(prefix=topic_prefix),
            "Power Manager External Control",
            "external_control",
            None,
            None,
            None,
            coordinator=None,
            translation_key="power_manager_external_control",
        ),
        MabwarpMqttSensor(
            entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=topic_prefix),
            "Power Manager Power At Meter",
            "power_at_meter",
            "W",
            SensorDeviceClass.POWER,
            None,
            coordinator=None,
            translation_key="power_manager_power_at_meter",
        ),
        MabwarpMqttSensor(
            entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=topic_prefix),
            "Power Manager Power Available",
            "power_available",
            "W",
            SensorDeviceClass.POWER,
            None,
            coordinator=None,
            translation_key="power_manager_power_available",
        ),
        MabwarpMqttSensor(
            entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=topic_prefix),
            "Power Manager Charging Blocked",
            "charging_blocked",
            None,
            None,
            None,
            coordinator=None,
            translation_key="power_manager_charging_blocked",
        ),
    ]
    return entities
