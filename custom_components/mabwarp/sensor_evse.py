# custom_components/mabwarp/sensor_evse.py

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
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
    TOPIC_EVSE_LOW_LEVEL,
    TOPIC_EVSE_STATE,
    TOPIC_METER_VALUES,
    TOPIC_NFC_LAST_TAG,
)
from .sensor_base import MabwarpMqttSensor, MeterValueCoordinator, async_subscribe


def build_evse_entities(
    entry,
    topic_prefix: str,
    coordinator: MeterValueCoordinator,
    features: list,
) -> list:
    """Build EVSE-related sensor entities."""
    entities = []
    has_meters = "meters" in features or not features
    if "meter" in features and "meters" not in features:
        has_meters = False
    has_nfc = "nfc" in features or not features

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
                translation_key="iec61851_state",
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
                translation_key="charger_state",
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
                0.001,
                translation_key="allowed_charging_current",
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
                translation_key="error_state",
            ),
        ]
    )

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
                translation_key="cp_pwm_duty_cycle",
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
                translation_key="uptime",
            ),
        ]
    )

    if has_meters:
        entities.extend(
            [
                MabwarpMqttSensor(
                    entry,
                    TOPIC_METER_VALUES.format(prefix=topic_prefix),
                    "Voltage L1",
                    METER_VALUE_ID_VOLTAGE_L1,
                    "V",
                    SensorDeviceClass.VOLTAGE,
                    None,
                    coordinator,
                    translation_key=METER_VALUE_ID_VOLTAGE_L1,
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
                    translation_key=METER_VALUE_ID_VOLTAGE_L2,
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
                    translation_key=METER_VALUE_ID_VOLTAGE_L3,
                ),
                MabwarpMqttSensor(
                    entry,
                    TOPIC_METER_VALUES.format(prefix=topic_prefix),
                    "Current L1",
                    METER_VALUE_ID_CURRENT_L1,
                    "A",
                    SensorDeviceClass.CURRENT,
                    None,
                    coordinator,
                    translation_key=METER_VALUE_ID_CURRENT_L1,
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
                    translation_key=METER_VALUE_ID_CURRENT_L2,
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
                    translation_key=METER_VALUE_ID_CURRENT_L3,
                ),
                MabwarpMqttSensor(
                    entry,
                    TOPIC_METER_VALUES.format(prefix=topic_prefix),
                    "Power L1",
                    METER_VALUE_ID_POWER_L1,
                    "W",
                    SensorDeviceClass.POWER,
                    None,
                    coordinator,
                    translation_key=METER_VALUE_ID_POWER_L1,
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
                    translation_key=METER_VALUE_ID_POWER_L2,
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
                    translation_key=METER_VALUE_ID_POWER_L3,
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
                    translation_key=METER_VALUE_ID_POWER_TOTAL,
                ),
                MabwarpMqttSensor(
                    entry,
                    TOPIC_METER_VALUES.format(prefix=topic_prefix),
                    "Energy (total)",
                    METER_VALUE_ID_ENERGY_TOTAL,
                    "kWh",
                    SensorDeviceClass.ENERGY,
                    SensorStateClass.TOTAL_INCREASING,
                    coordinator,
                    translation_key=METER_VALUE_ID_ENERGY_TOTAL,
                ),
            ]
        )

    if has_nfc:
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
                    translation_key="nfc_last_tag",
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
                    translation_key="nfc_last_seen",
                ),
            ]
        )

    return entities
