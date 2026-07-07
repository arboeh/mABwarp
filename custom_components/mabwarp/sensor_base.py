# custom_components/mabwarp/sensor_base.py

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.mqtt.client import async_subscribe
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    METER_VALUE_ID_CURRENT_L1,
    METER_VALUE_ID_CURRENT_L2,
    METER_VALUE_ID_CURRENT_L3,
    METER_VALUE_ID_ENERGY_TOTAL,
    METER_VALUE_ID_POWER_L1,
    METER_VALUE_ID_POWER_L2,
    METER_VALUE_ID_POWER_L3,
    METER_VALUE_ID_POWER_TOTAL,
    METER_VALUE_ID_VOLTAGE_L1,
    METER_VALUE_ID_VOLTAGE_L2,
    METER_VALUE_ID_VOLTAGE_L3,
)
from .entity_base import MabwarpEntityBase

_LOGGER = logging.getLogger(__name__)


class MeterValueCoordinator:
    """Coordinates meter value IDs with array indices."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._value_ids_mapping: dict[str, int] = {}
        self._values_data: dict[str, Any] = {}
        self._unsubscribe_value_ids = None
        self._unsubscribe_values = None

    def update_value_ids_mapping(self, value_ids: list) -> None:
        self._value_ids_mapping = {str(vid): idx for idx, vid in enumerate(value_ids)}
        _LOGGER.debug("Received value_ids mapping: %s", value_ids)

    def get_index(self, meter_value_id: str) -> int | None:
        return self._value_ids_mapping.get(str(meter_value_id))

    def store_values(self, values: list) -> None:
        _LOGGER.debug(
            "store_values: received %d values, mapping has %d entries", len(values), len(self._value_ids_mapping or [])
        )
        _LOGGER.debug("store_values raw payload: %s", values)
        if self._value_ids_mapping and len(values) != len(self._value_ids_mapping):
            _LOGGER.warning(
                "Meter values array length (%d) does not match value_ids "
                "mapping length (%d) — some sensors will show unknown",
                len(values),
                len(self._value_ids_mapping),
            )
        self._values_data = {str(vid): val for vid, val in enumerate(values) if str(vid) in self._value_ids_mapping}

    def set_unsubscribe_callbacks(self, unsubscribe_value_ids, unsubscribe_values) -> None:
        """Store MQTT unsubscribe callbacks for later cleanup."""
        self._unsubscribe_value_ids = unsubscribe_value_ids
        self._unsubscribe_values = unsubscribe_values


def check_plausibility(coordinator: MeterValueCoordinator) -> None:
    """Log warnings for implausible meter value combinations."""
    data = coordinator._values_data

    voltage_ids = [
        METER_VALUE_ID_VOLTAGE_L1,
        METER_VALUE_ID_VOLTAGE_L2,
        METER_VALUE_ID_VOLTAGE_L3,
    ]
    current_ids = [
        METER_VALUE_ID_CURRENT_L1,
        METER_VALUE_ID_CURRENT_L2,
        METER_VALUE_ID_CURRENT_L3,
    ]
    power_ids = [
        METER_VALUE_ID_POWER_L1,
        METER_VALUE_ID_POWER_L2,
        METER_VALUE_ID_POWER_L3,
    ]

    for vid_v, vid_i, vid_p in zip(voltage_ids, current_ids, power_ids, strict=True):
        voltage = data.get(vid_v)
        current = data.get(vid_i)
        power = data.get(vid_p)

        phase = voltage_ids.index(vid_v) + 1

        if voltage == 0 and current is not None and current > 1:
            _LOGGER.warning(
                "Implausible Messwertkombination: Phase %d, U=0V aber I=%.1fA",
                phase,
                current,
            )

        if power is not None and current is not None:
            if abs(power) < 1 and current > 5:
                _LOGGER.warning(
                    "Implausible Messwertkombination: Phase %d, P=%.1fW aber I=%.1fA",
                    phase,
                    power,
                    current,
                )


class MabwarpMqttSensor(MabwarpEntityBase, SensorEntity):
    """MQTT-based sensor for mABwarp integration."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        topic: str,
        name: str,
        field_path: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        coordinator: MeterValueCoordinator | None = None,
        conversion_factor: float | None = None,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the sensor.

        When ``translation_key`` is provided the entity name is resolved via the
        integration's translation files (prefixed with the device name). Otherwise
        ``name`` is used directly as a fallback (e.g. for dynamically discovered
        entities that cannot have a static translation key).
        """
        self._config_entry = config_entry
        self._topic = topic
        self._field_path = field_path
        self._coordinator = coordinator
        self._conversion_factor = conversion_factor
        self._unsubscribe = None

        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        if translation_key is None:
            self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                value = self.extract_field(data)
                if self._conversion_factor is not None and isinstance(value, int | float):
                    value = value * self._conversion_factor
                self._attr_native_value = value
                self._reset_parse_error_count()
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                KeyError,
                IndexError,
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

    def extract_field(self, data: dict) -> Any:
        """Extract nested field value using dot notation or array index."""
        if isinstance(data, list):
            if self._coordinator is not None:
                index = self._coordinator.get_index(self._field_path)
                if index is not None:
                    return data[index]
                return None
            return data[int(self._field_path)]
        keys = self._field_path.split(".")
        value: Any = data
        for key in keys:
            if isinstance(value, dict):
                value = value[key]
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                raise KeyError(f"Cannot access {key} on {type(value).__name__}")
        return value

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        safe_path = str(self._field_path).replace(".", "_")
        return self._build_unique_id(f"{self._topic.replace('/', '_')}_{safe_path}")
