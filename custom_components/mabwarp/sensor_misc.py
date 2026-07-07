# custom_components/mabwarp/sensor_misc.py

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
    TOPIC_CHARGE_MANAGER,
    TOPIC_INFO_DISPLAY_NAME,
    TOPIC_INFO_FEATURES,
    TOPIC_INFO_NAME,
    TOPIC_INFO_VERSION,
    TOPIC_P14A_ENWG_STATE,
    TOPIC_TEMPERATURES_STATE,
)
from .entity_base import MabwarpEntityBase
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpFeaturesSensor(MabwarpEntityBase, SensorEntity):
    """Sensor that reports the number of detected features."""

    _attr_icon = "mdi:format-list-checks"
    _attr_has_entity_name = True
    _attr_translation_key = "features"
    _attr_native_value = 0

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the features sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_INFO_FEATURES.format(prefix=topic_prefix)
        self._unsubscribe = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

        features = config_entry.data.get("features", [])
        self._attr_native_value = len(features)
        self._attr_extra_state_attributes = {"features": features}

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                if isinstance(data, list):
                    self._attr_native_value = len(data)
                    self._attr_extra_state_attributes = {"features": data}
                else:
                    self._attr_native_value = 0
                    self._attr_extra_state_attributes = {"features": []}
                self._reset_parse_error_count()
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
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
        return self._build_unique_id(f"{self._topic.replace('/', '_')}_features")


class MabwarpTemperatureSensor(MabwarpMqttSensor):
    """Sensor for temperature values."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        topic_prefix: str,
        name: str,
        field_name: str,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_TEMPERATURES_STATE.format(prefix=topic_prefix),
            name,
            field_name,
            "°C",
            SensorDeviceClass.TEMPERATURE,
            None,
            coordinator=None,
            translation_key=translation_key,
        )


class MabwarpP14aEnwgThrottledBinarySensor(MabwarpEntityBase, BinarySensorEntity):
    """Binary sensor for P14A ENWG throttling status."""

    _attr_icon = "mdi:speedometer"
    _attr_has_entity_name = True
    _attr_translation_key = "p14a_enwg_throttled"

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the binary sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_P14A_ENWG_STATE.format(prefix=topic_prefix)
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
                self._attr_is_on = bool(data.get("throttled", False))
                self._reset_parse_error_count()
                self.async_write_ha_state()
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
        """Return unique ID for this binary sensor."""
        return self._build_unique_id("p14a_enwg_throttled")


class MabwarpP14aEnwgMaxPowerSensor(MabwarpMqttSensor):
    """Sensor for P14A ENWG maximum allowed power."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_P14A_ENWG_STATE.format(prefix=topic_prefix),
            "P14A ENWG Max Power",
            "max_power",
            "W",
            SensorDeviceClass.POWER,
            None,
            coordinator=None,
            translation_key="p14a_enwg_max_power",
        )


def _discover_temperature_keys(
    hass: HomeAssistant,
    entry,
    topic_prefix: str,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Discover additional temperature keys dynamically."""
    temp_topic = TOPIC_TEMPERATURES_STATE.format(prefix=topic_prefix)
    future = asyncio.get_event_loop().create_future()
    discovered_keys = set()

    def _temp_message_received(msg: ReceiveMessage) -> None:
        if future.done():
            return
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, dict):
                keys = [k for k in data.keys() if k not in discovered_keys]
                if keys:
                    future.set_result(keys)
                else:
                    future.set_result([])
        except (json.JSONDecodeError, TypeError, ValueError):
            if not future.done():
                future.set_result([])

    async def _discover_temperature_keys():
        try:
            unsub = await async_subscribe(hass, temp_topic, _temp_message_received, 0)
        except HomeAssistantError as err:
            _LOGGER.warning("Failed to subscribe for temperature key discovery: %s", err)
            return

        try:
            new_keys = await asyncio.wait_for(future, timeout=5)
        except TimeoutError:
            new_keys = []
        finally:
            unsub()

        if new_keys:
            temp_entities = []
            for key in new_keys:
                discovered_keys.add(key)
                temp_entities.append(MabwarpTemperatureSensor(entry, topic_prefix, f"Temperature {key.title()}", key))
            if temp_entities:
                async_add_entities(temp_entities)

    hass.async_create_task(_discover_temperature_keys())


def build_misc_entities(
    hass: HomeAssistant,
    entry,
    topic_prefix: str,
    features: list,
    async_add_entities: AddEntitiesCallback,
) -> list:
    """Build miscellaneous sensor entities."""
    entities = []

    entities.append(MabwarpFeaturesSensor(entry, topic_prefix))

    entities.extend(
        [
            MabwarpMqttSensor(
                entry,
                TOPIC_INFO_VERSION.format(prefix=topic_prefix),
                "Firmware Version",
                "firmware",
                None,
                None,
                None,
                coordinator=None,
                translation_key="firmware_version",
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_INFO_NAME.format(prefix=topic_prefix),
                "Display Type",
                "display_type",
                None,
                None,
                None,
                coordinator=None,
                translation_key="display_type",
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_INFO_DISPLAY_NAME.format(prefix=topic_prefix),
                "Display Name",
                "display_name",
                None,
                None,
                None,
                coordinator=None,
                translation_key="display_name",
            ),
        ]
    )

    entities.extend(
        [
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Charge Manager State",
                "state",
                None,
                None,
                None,
                coordinator=None,
                translation_key="charge_manager_state",
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current Slot 0",
                "alloc.0",
                "A",
                SensorDeviceClass.CURRENT,
                None,
                None,
                0.001,
                translation_key="allocated_current_slot_0",
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current Slot 1",
                "alloc.1",
                "A",
                SensorDeviceClass.CURRENT,
                None,
                None,
                0.001,
                translation_key="allocated_current_slot_1",
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current Slot 2",
                "alloc.2",
                "A",
                SensorDeviceClass.CURRENT,
                None,
                None,
                0.001,
                translation_key="allocated_current_slot_2",
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current Slot 3",
                "alloc.3",
                "A",
                SensorDeviceClass.CURRENT,
                None,
                None,
                0.001,
                translation_key="allocated_current_slot_3",
            ),
        ]
    )

    has_temperatures = "temperatures" in features
    if has_temperatures:
        entities.append(
            MabwarpTemperatureSensor(entry, topic_prefix, "Temperature Current", "current", "temperature_current")
        )
        _discover_temperature_keys(hass, entry, topic_prefix, async_add_entities)

    has_p14a_enwg = "p14a_enwg" in features
    if has_p14a_enwg:
        entities.extend(
            [
                MabwarpP14aEnwgThrottledBinarySensor(entry, topic_prefix),
                MabwarpP14aEnwgMaxPowerSensor(entry, topic_prefix),
            ]
        )

    return entities
