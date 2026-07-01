# custom_components/mabwarp/sensor.py

from __future__ import annotations

import json
import logging
from typing import Any

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
    TOPIC_CHARGE_MANAGER,
    TOPIC_EVSE_LOW_LEVEL,
    TOPIC_EVSE_STATE,
    TOPIC_METER_VALUES,
    TOPIC_NFC_LAST_TAG,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp sensors."""
    topic_prefix = entry.data[CONF_TOPIC_PREFIX]

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
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "Charger State",
                "charger_state",
                None,
                None,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "Allowed Charging Current",
                "allowed_charging_current",
                "mA",
                None,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_STATE.format(prefix=topic_prefix),
                "Error State",
                "error_state",
                None,
                None,
                None,
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
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_EVSE_LOW_LEVEL.format(prefix=topic_prefix),
                "Uptime",
                "uptime",
                "s",
                None,
                None,
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
                "0",
                "V",
                SensorDeviceClass.VOLTAGE,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Voltage L2",
                "1",
                "V",
                SensorDeviceClass.VOLTAGE,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Voltage L3",
                "2",
                "V",
                SensorDeviceClass.VOLTAGE,
                None,
            ),
            # Current
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Current L1",
                "3",
                "A",
                SensorDeviceClass.CURRENT,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Current L2",
                "4",
                "A",
                SensorDeviceClass.CURRENT,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Current L3",
                "5",
                "A",
                SensorDeviceClass.CURRENT,
                None,
            ),
            # Power
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power L1",
                "6",
                "W",
                SensorDeviceClass.POWER,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power L2",
                "7",
                "W",
                SensorDeviceClass.POWER,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power L3",
                "8",
                "W",
                SensorDeviceClass.POWER,
                None,
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Power",
                "19",
                "W",
                SensorDeviceClass.POWER,
                None,
            ),
            # Energy
            MabwarpMqttSensor(
                entry,
                TOPIC_METER_VALUES.format(prefix=topic_prefix),
                "Energy (total)",
                "26",
                "kWh",
                SensorDeviceClass.ENERGY,
                SensorStateClass.TOTAL_INCREASING,
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
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_NFC_LAST_TAG.format(prefix=topic_prefix),
                "NFC Last Seen",
                "last_seen",
                None,
                SensorDeviceClass.TIMESTAMP,
                None,
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
            ),
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current",
                "allocated_current",
                "mA",
                None,
                None,
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
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = topic
        self._field_path = field_path
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

        self._unsubscribe = await self.hass.components.mqtt.async_subscribe(self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    def _extract_field(self, data: dict) -> Any:
        """Extract nested field value using dot notation or array index."""
        # data is a list (float array) for meter values
        if isinstance(data, list):
            return data[int(self._field_path)]
        # fallback for dict (evse/state etc.)
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
