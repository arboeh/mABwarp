# custom_components/mabwarp/sensor.py

from __future__ import annotations

import datetime
import json
import logging
from typing import Any

from homeassistant.components.mqtt.client import async_subscribe
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CHARGE_MODE_MAP,
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    CONFIG_ERROR_FLAG_BITS,
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
    TOPIC_CHARGE_TRACKER_CURRENT,
    TOPIC_CHARGE_TRACKER_LAST,
    TOPIC_CHARGE_TRACKER_STATE,
    TOPIC_EVSE_LOW_LEVEL,
    TOPIC_EVSE_STATE,
    TOPIC_INFO_DISPLAY_NAME,
    TOPIC_INFO_FEATURES,
    TOPIC_INFO_NAME,
    TOPIC_INFO_VERSION,
    TOPIC_METER_VALUE_IDS,
    TOPIC_METER_VALUES,
    TOPIC_NFC_LAST_TAG,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
    TOPIC_POWER_MANAGER_STATE,
    TOPIC_SOLAR_FORECAST_PLANES_CONFIG,
    TOPIC_SOLAR_FORECAST_PLANES_LIST,
    TOPIC_SOLAR_FORECAST_PLANES_STATE,
    TOPIC_SOLAR_FORECAST_STATE,
    TOPIC_CHARGE_LIMITS_STATE,
)

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

    def get_index(self, meter_value_id: str) -> int | None:
        return self._value_ids_mapping.get(meter_value_id)

    def store_values(self, values: list) -> None:
        self._values_data = {str(vid): val for vid, val in enumerate(values) if str(vid) in self._value_ids_mapping}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp sensors."""
    topic_prefix = entry.data[CONF_TOPIC_PREFIX]

    features = entry.data.get(CONF_FEATURES, [])
    has_meters = "meters" in features or not features
    if "meter" in features and "meters" not in features:
        has_meters = False
        _LOGGER.warning("Charger uses deprecated meter API, modern meters sensors skipped")
    has_nfc = "nfc" in features or not features
    has_charge_tracker = "charge_tracker" in features or not features

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

    async def values_message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, list):
                coordinator.store_values(data)
                _check_plausibility(coordinator)
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            _LOGGER.warning("Failed to parse values message: %s", err)

    coordinator._unsubscribe_value_ids = await async_subscribe(
        hass,
        TOPIC_METER_VALUE_IDS.format(prefix=topic_prefix),
        value_ids_message_received,
        0,
    )
    coordinator._unsubscribe_values = await async_subscribe(
        hass,
        TOPIC_METER_VALUES.format(prefix=topic_prefix),
        values_message_received,
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
                0.001,
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
    if has_meters:
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
                # ASSUMPTION (not yet verified against real hardware):
                # allocated_current is assumed to be in mA, analogous to
                # allowed_charging_current. TODO: verify with real payload
                # before first release.
                MabwarpMqttSensor(
                    entry,
                    TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                    "Allocated Current",
                    "allocated_current",
                    "A",
                    SensorDeviceClass.CURRENT,
                    None,
                    coordinator,
                    0.001,
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

    # Info sensors
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
            # ASSUMPTION (not yet verified against real hardware):
            # allocated_current is assumed to be in mA, analogous to
            # allowed_charging_current. TODO: verify with real payload
            # before first release.
            MabwarpMqttSensor(
                entry,
                TOPIC_CHARGE_MANAGER.format(prefix=topic_prefix),
                "Allocated Current",
                "allocated_current",
                "A",
                SensorDeviceClass.CURRENT,
                None,
                coordinator,
                0.001,
            ),
        ]
    )

    # Power Manager sensors
    has_power_manager = "power_manager" in features
    if has_power_manager:
        entities.extend(
            [
                # ASSUMPTION (not yet verified against real hardware):
                # Charge mode mapping 0=Standby, 1=Min, 2=PV, 3=Min+PV
                # is assumed analog to the WARP web interface.
                # TODO: verify with real payload before first release.
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
                ),
            ]
        )

    # Solar Forecast sensors
    has_solar_forecast = "solar_forecast" in features
    if has_solar_forecast:
        solar_forecast_entities = [
            MabwarpSolarForecastValueSensor(entry, topic_prefix, "wh_today"),
            MabwarpSolarForecastValueSensor(entry, topic_prefix, "wh_today_remaining"),
            MabwarpSolarForecastValueSensor(entry, topic_prefix, "wh_tomorrow"),
        ]
        entities.extend(solar_forecast_entities)

        async def _discover_solar_planes():
            future = asyncio.get_event_loop().create_future()

            def _planes_list_received(msg) -> None:
                try:
                    payload = msg.payload
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")
                    data = json.loads(payload)
                    if isinstance(data, list):
                        future.set_result([int(x) for x in data])
                    else:
                        future.set_result([])
                except (json.JSONDecodeError, TypeError, ValueError):
                    future.set_result([])

            unsub = await async_subscribe(
                hass,
                TOPIC_SOLAR_FORECAST_PLANES_LIST.format(prefix=topic_prefix),
                _planes_list_received,
                0,
            )
            try:
                plane_indices = await asyncio.wait_for(future, timeout=3)
            except TimeoutError:
                plane_indices = []
            finally:
                unsub()

            if not plane_indices:
                for idx in range(10):
                    fut = asyncio.get_event_loop().create_future()

                    def _make_callback(f, i):
                        def _plane_received(msg) -> None:
                            try:
                                payload = msg.payload
                                if isinstance(payload, bytes):
                                    payload = payload.decode("utf-8")
                                data = json.loads(payload)
                                if isinstance(data, dict) and "place" in data:
                                    f.set_result(i)
                                else:
                                    f.set_result(None)
                            except (json.JSONDecodeError, TypeError, ValueError):
                                f.set_result(None)
                        return _plane_received

                    unsub2 = await async_subscribe(
                        hass,
                        TOPIC_SOLAR_FORECAST_PLANES_STATE.format(prefix=topic_prefix, idx=idx),
                        _make_callback(fut, idx),
                        0,
                    )
                    try:
                        result = await asyncio.wait_for(fut, timeout=0.5)
                        if result is not None:
                            plane_indices.append(result)
                    except TimeoutError:
                        pass
                    finally:
                        unsub2()

            plane_entities = []
            for idx in plane_indices:
                plane_entities.extend([
                    MabwarpSolarPlaneStateSensor(entry, topic_prefix, idx),
                    MabwarpSolarPlaneConfigSensor(entry, topic_prefix, idx),
                ])

            if plane_entities:
                async_add_entities(plane_entities)

        hass.create_task(_discover_solar_planes())

    # Charge Limits sensors
    has_charge_limits = "charge_limits" in features
    if has_charge_limits:
        entities.extend(
            [
                MabwarpChargeLimitsTimestampSensor(
                    entry,
                    topic_prefix,
                    "Charge Limits Start Timestamp",
                    "start_timestamp_ms",
                ),
                MabwarpChargeLimitsTimestampSensor(
                    entry,
                    topic_prefix,
                    "Charge Limits Target Timestamp",
                    "target_timestamp_ms",
                ),
                MabwarpChargeLimitsEnergySensor(
                    entry,
                    topic_prefix,
                    "Charge Limits Start Energy",
                    "start_energy_kwh",
                    "kWh",
                ),
                MabwarpChargeLimitsEnergySensor(
                    entry,
                    topic_prefix,
                    "Charge Limits Target Energy",
                    "target_energy_kwh",
                    "kWh",
                ),
            ]
        )

    # Features sensor
    entities.append(MabwarpFeaturesSensor(entry, topic_prefix))

    # Charge tracker sensors
    if has_charge_tracker:
        entities.extend(
            [
                MabwarpMqttSensor(
                    entry,
                    TOPIC_CHARGE_TRACKER_STATE.format(prefix=topic_prefix),
                    "Tracked Charges",
                    "tracked_charges",
                    None,
                    None,
                    None,
                    coordinator=None,
                ),
                MabwarpMqttSensor(
                    entry,
                    TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=topic_prefix),
                    "Current Charge Meter Start",
                    "meter_start",
                    "kWh",
                    SensorDeviceClass.ENERGY,
                    None,
                    coordinator=None,
                ),
                MabwarpCurrentChargeUserIDSensor(entry, topic_prefix),
                MabwarpLastChargeSensor(entry, topic_prefix),
            ]
        )

    async_add_entities(entities)


def _check_plausibility(coordinator: MeterValueCoordinator) -> None:
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
        conversion_factor: float | None = None,
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = topic
        self._field_path = field_path
        self._coordinator = coordinator
        self._conversion_factor = conversion_factor
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
                value = self.extract_field(data)
                if self._conversion_factor is not None and isinstance(value, int | float):
                    value = value * self._conversion_factor
                self._attr_native_value = value
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                KeyError,
                IndexError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

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


class MabwarpFeaturesSensor(SensorEntity):
    """Sensor that reports the number of detected features."""

    _attr_icon = "mdi:format-list-checks"
    _attr_native_value = 0
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the features sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_INFO_FEATURES.format(prefix=topic_prefix)
        self._unsubscribe = None

        features = config_entry.data.get(CONF_FEATURES, [])
        self._attr_native_value = len(features)
        self._attr_extra_state_attributes = {"features": features}

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
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
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse features message: %s", err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_features"

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


class MabwarpCurrentChargeUserIDSensor(MabwarpMqttSensor):
    """Sensor for current charge user ID with idle-state handling."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=topic_prefix),
            "Current Charge User ID",
            "user_id",
            None,
            None,
            None,
            coordinator=None,
        )

    def extract_field(self, data: dict) -> Any:
        value = super().extract_field(data)
        return None if value == -1 else value


class MabwarpLastChargeSensor(SensorEntity):
    """Sensor for the most recent entry in charge_tracker/last_charges."""

    _attr_icon = "mdi:ev-station"
    _attr_native_value = None
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the last charge sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_CHARGE_TRACKER_LAST.format(prefix=topic_prefix)
        self._unsubscribe = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                if not isinstance(data, list) or len(data) == 0:
                    self._attr_native_value = None
                    self._attr_extra_state_attributes = {}
                    _LOGGER.warning("Received empty last_charges array")
                    self.async_write_ha_state()
                    return
                last = data[-1]
                energy = last.get("energy_charged")
                self._attr_native_value = energy
                self._attr_extra_state_attributes = {
                    "charge_duration": last.get("charge_duration"),
                    "user_id": last.get("user_id"),
                    "timestamp": datetime.datetime.fromtimestamp(
                        last.get("timestamp_minutes", 0) * 60,
                        tz=datetime.UTC,
                    ).isoformat(),
                }
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
                KeyError,
            ) as err:
                _LOGGER.warning("Failed to parse last_charges message: %s", err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_last_charge"

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


class MabwarpChargeModeSensor(SensorEntity):
    """Sensor for WARP Power Manager charge mode with text mapping."""

    _attr_icon = "mdi:ev-station"
    _attr_native_value = None
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_POWER_MANAGER_CHARGE_MODE.format(prefix=topic_prefix)
        self._unsubscribe = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                mode = data.get("mode")
                if mode is not None:
                    self._attr_native_value = CHARGE_MODE_MAP.get(int(mode), f"Unknown ({mode})")
                    self._attr_extra_state_attributes = {"mode": int(mode)}
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_charge_mode"

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


class MabwarpConfigErrorFlagsSensor(SensorEntity):
    """Sensor for WARP Power Manager config error flags with bit decoding."""

    _attr_icon = "mdi:alert-circle"
    _attr_native_value = None
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_POWER_MANAGER_STATE.format(prefix=topic_prefix)
        self._unsubscribe = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
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
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_config_error_flags"

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


class MabwarpSolarForecastValueSensor(MabwarpMqttSensor):
    """Sensor for solar forecast values with -1 => None mapping."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, field_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_SOLAR_FORECAST_STATE.format(prefix=topic_prefix),
            f"Solar Forecast {field_name.replace('_', ' ').title()}",
            field_name,
            "Wh",
            SensorDeviceClass.ENERGY,
            None,
            coordinator=None,
        )

    def extract_field(self, data: dict) -> Any:
        value = super().extract_field(data)
        return None if value == -1 else value


class MabwarpSolarPlaneStateSensor(MabwarpMqttSensor):
    """Sensor for a single solar plane's state (place)."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, plane_idx: int) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_SOLAR_FORECAST_PLANES_STATE.format(prefix=topic_prefix, idx=plane_idx),
            f"Solar Plane {plane_idx} Place",
            "place",
            None,
            None,
            None,
            coordinator=None,
        )


class MabwarpSolarPlaneConfigSensor(SensorEntity):
    """Sensor for a single solar plane's config (name, wp)."""

    _attr_native_value = None
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, plane_idx: int) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_SOLAR_FORECAST_PLANES_CONFIG.format(prefix=topic_prefix, idx=plane_idx)
        self._unsubscribe = None
        self._plane_idx = plane_idx

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_native_value = data.get("wp")
                self._attr_extra_state_attributes = {
                    "name": data.get("name"),
                    "place": data.get("place"),
                }
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_solar_plane_{self._plane_idx}_config"

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


class MabwarpChargeLimitsTimestampSensor(SensorEntity):
    """Sensor for charge limits timestamps (ms -> datetime)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_native_value = None

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, name: str, field_name: str) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_CHARGE_LIMITS_STATE.format(prefix=topic_prefix)
        self._field_name = field_name
        self._unsubscribe = None
        self._attr_name = name

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                value = data.get(self._field_name)
                if value is not None:
                    self._attr_native_value = datetime.datetime.fromtimestamp(
                        int(value) / 1000, tz=datetime.UTC
                    )
                else:
                    self._attr_native_value = None
                self.async_write_ha_state()
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        safe_field = self._field_name.replace(".", "_")
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_{safe_field}"

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


class MabwarpChargeLimitsEnergySensor(MabwarpMqttSensor):
    """Sensor for charge limits energy values with null handling."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, name: str, field_name: str, unit: str) -> None:
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
        )

    def extract_field(self, data: dict) -> Any:
        value = super().extract_field(data)
        return None if value is None else value
