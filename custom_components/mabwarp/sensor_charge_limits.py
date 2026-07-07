# custom_components/mabwarp/sensor_charge_limits.py

from __future__ import annotations

import datetime
import json
import logging
from typing import Any

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
    TOPIC_CHARGE_LIMITS_STATE,
)
from .entity_base import MabwarpEntityBase
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpChargeLimitsTimestampSensor(MabwarpEntityBase, SensorEntity):
    """Sensor for charge limits timestamps (ms -> datetime)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_native_value = None

    def __init__(
        self,
        config_entry: ConfigEntry,
        topic_prefix: str,
        name: str,
        field_name: str,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_CHARGE_LIMITS_STATE.format(prefix=topic_prefix)
        self._field_name = field_name
        self._unsubscribe = None
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                value = data.get(self._field_name)
                if value is not None:
                    self._attr_native_value = datetime.datetime.fromtimestamp(int(value) / 1000, tz=datetime.UTC)
                else:
                    self._attr_native_value = None
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
        safe_field = self._field_name.replace(".", "_")
        return self._build_unique_id(f"{self._topic.replace('/', '_')}_{safe_field}")


class MabwarpChargeLimitsEnergySensor(MabwarpMqttSensor):
    """Sensor for charge limits energy values with null handling."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        topic_prefix: str,
        name: str,
        field_name: str,
        unit: str,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_CHARGE_LIMITS_STATE.format(prefix=topic_prefix),
            name,
            field_name,
            unit,
            SensorDeviceClass.ENERGY,
            None,
            coordinator=None,
            translation_key=translation_key,
        )

    def extract_field(self, data: dict) -> Any:
        value = super().extract_field(data)
        return None if value is None else value


def build_charge_limits_entities(entry, topic_prefix: str, features: list) -> list:
    """Build charge limits sensor entities."""
    has_charge_limits = "charge_limits" in features
    if not has_charge_limits:
        return []

    entities = [
        MabwarpChargeLimitsTimestampSensor(
            entry,
            topic_prefix,
            "Charge Limits Start Timestamp",
            "start_timestamp_ms",
            "charge_limits_start_timestamp_ms",
        ),
        MabwarpChargeLimitsTimestampSensor(
            entry,
            topic_prefix,
            "Charge Limits Target Timestamp",
            "target_timestamp_ms",
            "charge_limits_target_timestamp_ms",
        ),
        MabwarpChargeLimitsEnergySensor(
            entry,
            topic_prefix,
            "Charge Limits Start Energy",
            "start_energy_kwh",
            "kWh",
            "charge_limits_start_energy_kwh",
        ),
        MabwarpChargeLimitsEnergySensor(
            entry,
            topic_prefix,
            "Charge Limits Target Energy",
            "target_energy_kwh",
            "kWh",
            "charge_limits_target_energy_kwh",
        ),
    ]
    return entities
