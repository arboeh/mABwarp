# custom_components/mabwarp/sensor.py

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DOMAIN,
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
    TOPIC_CHARGE_MANAGER,
    TOPIC_EVSE_LOW_LEVEL,
    TOPIC_EVSE_STATE,
    TOPIC_METER_VALUES,
    TOPIC_METER_VALUE_IDS,
    TOPIC_NFC_LAST_TAG,
)

_LOGGER = logging.getLogger(__name__)


class MeterValueCoordinator:
    """Coordinates meter value IDs with array indices."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._value_ids_mapping: dict[str, int] = {}
        self._unsubscribe_value_ids = None

    def update_value_ids_mapping(self, value_ids: list) -> None:
        self._value_ids_mapping = {str(vid): idx for idx, vid in enumerate(value_ids)}

    def get_index(self, meter_value_id: str) -> int | None:
        return self._value_ids_mapping.get(meter_value_id)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp sensors."""
    topic_prefix = entry.data[CONF_TOPIC_PREFIX]

    coordinator = MeterValueCoordinator(hass)

    async def value_ids_message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, list):
                coordinator.update_value_ids_mapping(data)
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            _LOGGER.warning("Failed to parse value_ids message: %s", err)

    coordinator._unsubscribe_value_ids = await mqtt.async_subscribe(
        hass,
        TOPIC_METER_VALUE_IDS.format(prefix=topic_prefix),
        value_ids_message_received,
        0,
    )

    entities = []

    # EVSE state sensors
    entities.extend(
        [
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "IEC61851 State",
                "iec61851_state",
                None,
                None,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "Charger State",
                "charger_state",
                None,
                None,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "Allowed Charging Current",
                "allowed_charging_current",
                "A",
                SensorDeviceClass.CURRENT,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "Error State",
                "error_state",
                None,
                None,
                None,
                coordinator,
            ),
        ]
    )

    # EVSE low level state sensors
    entities.extend(
        [
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_LOW_LEVEL.format(prefix=topic_prefix),
                "CP PWM Duty Cycle",
                "cp_pwm_duty_cycle",
                "%",
                None,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_LOW_LEVEL.format(prefix=topic_prefix),
                "Uptime",
                "uptime",
                "s",
                None,
                None,
                coordinator,
            ),
        ]
    )

    # Meter values sensors
    entities.extend(
        [
            # Voltage
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Voltage L1",
                METER_VALUE_ID_VOLTAGE_L1,
                "V",
                SensorDeviceClass.VOLTAGE,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Voltage L2",
                METER_VALUE_ID_VOLTAGE_L2,
                "V",
                SensorDeviceClass.VOLTAGE,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Voltage L3",
                METER_VALUE_ID_VOLTAGE_L3,
                "V",
                SensorDeviceClass.VOLTAGE,
                None,
                coordinator,
            ),
            # Current
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Current L1",
                METER_VALUE_ID_CURRENT_L1,
                "A",
                SensorDeviceClass.CURRENT,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Current L2",
                METER_VALUE_ID_CURRENT_L2,
                "A",
                SensorDeviceClass.CURRENT,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Current L3",
                METER_VALUE_ID_CURRENT_L3,
                "A",
                SensorDeviceClass.CURRENT,
                None,
                coordinator,
            ),
            # Power
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power L1",
                METER_VALUE_ID_POWER_L1,
                "W",
                SensorDeviceClass.POWER,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power L2",
                METER_VALUE_ID_POWER_L2,
                "W",
                SensorDeviceClass.POWER,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power L3",
                METER_VALUE_ID_POWER_L3,
                "W",
                SensorDeviceClass.POWER,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power",
                METER_VALUE_ID_POWER_TOTAL,
                "W",
                SensorDeviceClass.POWER,
                None,
                coordinator,
            ),
            # Energy
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Energy (total)",
                METER_VALUE_ID_ENERGY_TOTAL,
                "kWh",
                SensorDeviceClass.ENERGY,
                SensorStateClass.TOTAL_INCREASING,
                coordinator,
            ),
        ]
    )

    # NFC last seen sensors
    entities.extend(
        [
            MabwarpMqttSensor(
                entry,
                TOPIC_NFC_LAST_TAG.format(prefix=topic_prefix),
                "NFC Last Tag",
                "tag_id",
                None,
                None,
                None,
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_NFC_LAST_TAG.format(prefix=topic_prefix),
                "NFC Last Seen",
                "last_seen",
                None,
                SensorDeviceClass.TIMESTAMP,
                None,
                coordinator,
            ),
        ]
    )

    # Charge manager state sensors
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
                coordinator,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current",
                "allocated_current",
                "mA",
                None,
                None,
                coordinator,
            ),
        ]
    )

    async_add_entities(entities)


class MabwarpMqttSensor(SensorEntity):
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
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = topic
        self._field_path = field_path
        self._coordinator = coordinator
        self._unsubscribe = None

        self._attr_name = f"WARP {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                value = self._extract_field(data)
                self._attr_native_value = value
                self.async_write_ha_state()
            except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        self._unsubscribe = await mqtt.async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    def _extract_field(self, data: dict) -> Any:
        """Extract nested field value using dot notation or array index."""
        if isinstance(data, list):
            if self._coordinator is not None:
                index = self._coordinator.get_index(self._field_path)
                if index is not None:
                    return data[index]
                return "unknown"
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
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        safe_path = self._field_path.replace(".", "_")
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_{safe_path}"

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
