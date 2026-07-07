# custom_components/mabwarp/number.py

from __future__ import annotations

import json
import logging

from homeassistant.components.mqtt.client import async_publish, async_subscribe
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
    TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS,
    TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS_UPDATE,
    TOPIC_EVSE_EXT_CURRENT,
    TOPIC_EVSE_SET_EXT_CURRENT,
)
from .entity_base import MabwarpEntityBase
from .features import Feature, has_feature

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp numbers."""
    entities = [MabwarpChargingCurrentNumber(entry)]
    features = entry.data.get("features", [])
    if has_feature(features, Feature.CHARGE_LIMITS):
        entities.extend(
            [
                MabwarpChargeLimitsDurationNumber(entry),
                MabwarpChargeLimitsEnergyNumber(entry),
            ]
        )
    async_add_entities(entities)


class MabwarpChargingCurrentNumber(MabwarpEntityBase, NumberEntity):
    """Number entity for setting the external charging current limit."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging_current_limit"
    _attr_native_min_value = 0
    _attr_native_max_value = 32
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "A"
    _attr_icon = "mdi:current-ac"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_native_value = 0.0

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_native_value = float(data["current"]) / 1000
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
                self._handle_parse_error(err, self._topic)

        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        self._topic = TOPIC_EVSE_EXT_CURRENT.format(prefix=topic_prefix)
        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        topic = TOPIC_EVSE_SET_EXT_CURRENT.format(prefix=topic_prefix)
        payload = json.dumps({"current": int(value * 1000)})
        await async_publish(
            self.hass,
            topic,
            payload,
            qos=0,
            retain=False,
            encoding="utf-8",
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        """Return unique ID for this number entity."""
        return self._build_unique_id("charging_current_limit")


class MabwarpChargeLimitsDurationNumber(MabwarpEntityBase, NumberEntity):
    """Number entity for charge limits default duration."""

    _attr_has_entity_name = True
    _attr_translation_key = "charge_limits_duration"
    _attr_native_min_value = 0
    _attr_native_max_value = 24
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:timer"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_native_value = 0.0

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_native_value = float(data.get("duration", 0))
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
                self._handle_parse_error(err, self._topic)

        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        self._topic = TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS.format(prefix=topic_prefix)
        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        topic = TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS_UPDATE.format(prefix=topic_prefix)
        payload = json.dumps({"duration": value})
        await async_publish(
            self.hass,
            topic,
            payload,
            qos=0,
            retain=False,
            encoding="utf-8",
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        """Return unique ID for this number entity."""
        return self._build_unique_id("charge_limits_duration")


class MabwarpChargeLimitsEnergyNumber(MabwarpEntityBase, NumberEntity):
    """Number entity for charge limits default energy."""

    _attr_has_entity_name = True
    _attr_translation_key = "charge_limits_energy_wh"
    _attr_native_min_value = 0
    _attr_native_max_value = 100000
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "Wh"
    _attr_icon = "mdi:lightning-bolt"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_native_value = 0.0

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_native_value = float(data.get("energy_wh", 0))
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
                self._handle_parse_error(err, self._topic)

        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        self._topic = TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS.format(prefix=topic_prefix)
        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        topic = TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS_UPDATE.format(prefix=topic_prefix)
        payload = json.dumps({"energy_wh": value})
        await async_publish(
            self.hass,
            topic,
            payload,
            qos=0,
            retain=False,
            encoding="utf-8",
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        """Return unique ID for this number entity."""
        return self._build_unique_id("charge_limits_energy_wh")
