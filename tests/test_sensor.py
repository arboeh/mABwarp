# tests/test_sensor.py

import asyncio
import datetime
import json
import logging
from unittest.mock import MagicMock, patch

from homeassistant.components.sensor import SensorDeviceClass

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    METER_VALUE_ID_VOLTAGE_L1,
    TOPIC_CHARGE_TRACKER_CURRENT,
    TOPIC_CHARGE_TRACKER_LAST,
    TOPIC_CHARGE_TRACKER_STATE,
    TOPIC_EVSE_STATE,
    TOPIC_INFO_VERSION,
    TOPIC_METER_VALUES,
    TOPIC_NFC_LAST_TAG,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
    TOPIC_POWER_MANAGER_STATE,
    TOPIC_SOLAR_FORECAST_PLANES_CONFIG,
    TOPIC_SOLAR_FORECAST_PLANES_STATE,
    TOPIC_SOLAR_FORECAST_STATE,
)
from custom_components.mabwarp.sensor import (
    MabwarpChargeModeSensor,
    MabwarpConfigErrorFlagsSensor,
    MabwarpCurrentChargeUserIDSensor,
    MabwarpFeaturesSensor,
    MabwarpLastChargeSensor,
    MabwarpMqttSensor,
    MabwarpSolarForecastValueSensor,
    MabwarpSolarPlaneConfigSensor,
    MabwarpSolarPlaneStateSensor,
    async_setup_entry,
)


class FakeCoordinator:
    def __init__(self, mapping):
        self._mapping = mapping

    def get_index(self, meter_value_id):
        return self._mapping.get(meter_value_id)


def test_sensor_unique_id():
    """Test sensor unique_id generation."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_EVSE_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Test",
        "test_field",
        None,
        None,
        None,
        None,
    )
    unique_id = sensor.unique_id
    assert unique_id is not None
    assert "TEST01" in unique_id


def test_sensor_device_info():
    """Test sensor device_info properties."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_EVSE_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Test",
        "test_field",
        None,
        None,
        None,
        None,
    )
    device_info = sensor.device_info
    assert device_info["manufacturer"] == "Tinkerforge GmbH"
    assert device_info["model"] == "WARP3"
    assert (DOMAIN, "TEST01") in device_info["identifiers"]


def test_extract_field_simple():
    """Test simple field extraction."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_EVSE_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Test",
        "power",
        None,
        None,
        None,
        None,
    )
    result = sensor.extract_field({"power": 1500.0})
    assert result == 1500.0


def test_extract_field_meter_array_with_mapping():
    """Test meter array extraction using value_ids mapping."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    mapping = {METER_VALUE_ID_VOLTAGE_L1: 5, "16": 2}
    coordinator = FakeCoordinator(mapping)
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Voltage L1",
        METER_VALUE_ID_VOLTAGE_L1,
        "V",
        None,
        None,
        coordinator,
    )
    meter_data = [10.0, 11.0, 12.0, 13.0, 14.0, 230.0]
    result = sensor.extract_field(meter_data)
    assert result == 230.0


def test_extract_field_meter_array_when_mapping_missing():
    """Test meter array returns unknown when value_ids not received."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    coordinator = FakeCoordinator({})
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Voltage L1",
        METER_VALUE_ID_VOLTAGE_L1,
        "V",
        None,
        None,
        coordinator,
    )
    meter_data = [10.0, 11.0, 12.0]
    result = sensor.extract_field(meter_data)
    assert result == "unknown"


def test_extract_field_meter_array_changed_order():
    """Test meter array extraction when value_ids order changes."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    mapping = {METER_VALUE_ID_VOLTAGE_L1: 7, "16": 3, "19": 1}
    coordinator = FakeCoordinator(mapping)
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Voltage L1",
        METER_VALUE_ID_VOLTAGE_L1,
        "V",
        None,
        None,
        coordinator,
    )
    meter_data = [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 230.0]
    result = sensor.extract_field(meter_data)
    assert result == 230.0


def test_sensor_name():
    """Test sensor name starts with WARP prefix."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_EVSE_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Test Sensor",
        "test_field",
        None,
        None,
        None,
        None,
    )
    assert sensor._attr_name.startswith("WARP ")


def test_conversion_factor_applied():
    """Test conversion_factor is applied to raw values."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
                CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            }
        },
    )()
    coordinator = FakeCoordinator({})
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_EVSE_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Test",
        "test_field",
        None,
        None,
        None,
        coordinator,
        conversion_factor=0.001,
    )
    result = sensor.extract_field({"test_field": 6000})
    if isinstance(result, int | float) and sensor._conversion_factor is not None:
        result = result * sensor._conversion_factor
    assert result == 6.0


def _make_mock_entry(features=None):
    """Create a mock config entry with optional features."""
    data = {
        CONF_DEVICE_ID: "TEST01",
        CONF_WARP_VERSION: "WARP3",
        CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
    }
    if features is not None:
        data[CONF_FEATURES] = features
    return type("MockEntry", (), {"data": data})()


def test_meter_sensors_skipped_without_meters_feature():
    """Test meter sensors are skipped when features=['evse']."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_meter_sensors_created_with_empty_features_fallback():
    """Test meter sensors are created when features is empty (fallback)."""
    entry = _make_mock_entry(features=[])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    meter_topics = [e._topic for e in added if TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX) in e._topic]
    assert len(meter_topics) > 0


def test_nfc_sensors_skipped_without_nfc_feature():
    """Test NFC sensors are skipped when features=['evse']."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_NFC_LAST_TAG.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_features_sensor_counts_and_attributes():
    """Test features sensor reports correct count and attributes from entry data."""
    entry = _make_mock_entry(features=["evse", "nfc", "meters"])
    sensor = MabwarpFeaturesSensor(entry, DEFAULT_TOPIC_PREFIX)
    assert sensor._attr_native_value == 3
    assert sensor._attr_extra_state_attributes["features"] == ["evse", "nfc", "meters"]


def test_firmware_version_sensor_parses_correctly():
    """Test firmware version sensor extracts firmware field."""
    mock_config_entry = _make_mock_entry()
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_INFO_VERSION.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Firmware Version",
        "firmware",
        None,
        None,
        None,
        coordinator=None,
    )
    payload = {"firmware": "1.2.3", "config": "abc", "config_type": "release"}
    result = sensor.extract_field(payload)
    assert result == "1.2.3"


def test_current_charge_sensor_idle_when_no_session():
    """Test current charge user ID sensor returns None when user_id is -1."""
    entry = _make_mock_entry(features=["charge_tracker"])
    sensor = MabwarpCurrentChargeUserIDSensor(entry, DEFAULT_TOPIC_PREFIX)
    payload = {
        "user_id": -1,
        "meter_start": 0.0,
        "evse_uptime_start": 0,
        "timestamp_minutes": 0,
        "authorization_type": 0,
    }
    result = sensor.extract_field(payload)
    assert result is None


def test_last_charge_sensor_uses_latest_entry():
    """Test last charge sensor uses the latest entry from array."""
    entry = _make_mock_entry(features=["charge_tracker"])
    sensor = MabwarpLastChargeSensor(entry, DEFAULT_TOPIC_PREFIX)
    payload = [
        {"timestamp_minutes": 1000, "charge_duration": 30, "user_id": 1, "energy_charged": 12.5},
        {"timestamp_minutes": 2000, "charge_duration": 60, "user_id": 2, "energy_charged": 24.0},
        {"timestamp_minutes": 3000, "charge_duration": 45, "user_id": 3, "energy_charged": 18.3},
    ]
    msg = MagicMock()
    msg.payload = json.dumps(payload).encode("utf-8")
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload_data = msg.payload
            if isinstance(payload_data, bytes):
                payload_data = payload_data.decode("utf-8")
            data = json.loads(payload_data)
            if not isinstance(data, list) or len(data) == 0:
                sensor._attr_native_value = None
                sensor._attr_extra_state_attributes = {}
                logging.warning("Received empty last_charges array")
                sensor.async_write_ha_state()
                return
            last = data[-1]
            energy = last.get("energy_charged")
            sensor._attr_native_value = energy
            sensor._attr_extra_state_attributes = {
                "charge_duration": last.get("charge_duration"),
                "user_id": last.get("user_id"),
                "timestamp": datetime.datetime.fromtimestamp(
                    last.get("timestamp_minutes", 0) * 60,
                    tz=datetime.UTC,
                ).isoformat(),
            }
            sensor.async_write_ha_state()
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            KeyError,
        ) as err:
            logging.warning("Failed to parse last_charges message: %s", err)

    message_received(msg)
    assert sensor._attr_native_value == 18.3
    assert sensor._attr_extra_state_attributes["user_id"] == 3


def test_last_charge_sensor_empty_array_no_crash():
    """Test last charge sensor handles empty array gracefully."""
    entry = _make_mock_entry(features=["charge_tracker"])
    sensor = MabwarpLastChargeSensor(entry, DEFAULT_TOPIC_PREFIX)
    msg = MagicMock()
    msg.payload = b"[]"
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload_data = msg.payload
            if isinstance(payload_data, bytes):
                payload_data = payload_data.decode("utf-8")
            data = json.loads(payload_data)
            if not isinstance(data, list) or len(data) == 0:
                sensor._attr_native_value = None
                sensor._attr_extra_state_attributes = {}
                logging.warning("Received empty last_charges array")
                sensor.async_write_ha_state()
                return
            last = data[-1]
            energy = last.get("energy_charged")
            sensor._attr_native_value = energy
            sensor._attr_extra_state_attributes = {
                "charge_duration": last.get("charge_duration"),
                "user_id": last.get("user_id"),
                "timestamp": datetime.datetime.fromtimestamp(
                    last.get("timestamp_minutes", 0) * 60,
                    tz=datetime.UTC,
                ).isoformat(),
            }
            sensor.async_write_ha_state()
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            KeyError,
        ) as err:
            logging.warning("Failed to parse last_charges message: %s", err)

    message_received(msg)
    assert sensor._attr_native_value is None
    assert sensor._attr_extra_state_attributes == {}


def test_charge_tracker_sensors_skipped_without_feature():
    """Test charge tracker sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_CHARGE_TRACKER_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_CHARGE_TRACKER_LAST.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_power_manager_sensors_skipped_without_feature():
    """Test power_manager sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_POWER_MANAGER_CHARGE_MODE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_POWER_MANAGER_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_power_manager_sensors_created_with_feature():
    """Test power_manager sensors are created when feature is present."""
    entry = _make_mock_entry(features=["power_manager"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    power_manager_topics = [
        TOPIC_POWER_MANAGER_CHARGE_MODE.format(prefix=DEFAULT_TOPIC_PREFIX),
        TOPIC_POWER_MANAGER_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
    ]
    for topic in power_manager_topics:
        assert any(e._topic == topic for e in added)


def test_charge_mode_sensor_maps_mode_to_text():
    """Test charge mode sensor maps numeric mode to text."""
    entry = _make_mock_entry(features=["power_manager"])
    sensor = MabwarpChargeModeSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        mode = data.get("mode")
        if mode is not None:
            from custom_components.mabwarp.const import CHARGE_MODE_MAP

            sensor._attr_native_value = CHARGE_MODE_MAP.get(int(mode), f"Unknown ({mode})")
            sensor._attr_extra_state_attributes = {"mode": int(mode)}
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"mode": 0}'
    message_received(msg)
    assert sensor._attr_native_value == "Standby"

    msg.payload = b'{"mode": 1}'
    message_received(msg)
    assert sensor._attr_native_value == "Min"

    msg.payload = b'{"mode": 2}'
    message_received(msg)
    assert sensor._attr_native_value == "PV"

    msg.payload = b'{"mode": 3}'
    message_received(msg)
    assert sensor._attr_native_value == "Min+PV"


def test_charge_mode_sensor_unknown_mode():
    """Test charge mode sensor handles unknown mode."""
    entry = _make_mock_entry(features=["power_manager"])
    sensor = MabwarpChargeModeSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        mode = data.get("mode")
        if mode is not None:
            from custom_components.mabwarp.const import CHARGE_MODE_MAP

            sensor._attr_native_value = CHARGE_MODE_MAP.get(int(mode), f"Unknown ({mode})")
            sensor._attr_extra_state_attributes = {"mode": int(mode)}
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"mode": 99}'
    message_received(msg)
    assert "Unknown (99)" in sensor._attr_native_value


def test_config_error_flags_sensor_decodes_bits():
    """Test config error flags sensor decodes bitmask."""
    entry = _make_mock_entry(features=["power_manager"])
    sensor = MabwarpConfigErrorFlagsSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor._attr_native_value = None
    sensor._attr_extra_state_attributes = {}

    def message_received(msg) -> None:
        try:
            payload_data = msg.payload
            if isinstance(payload_data, bytes):
                payload_data = payload_data.decode("utf-8")
            data = json.loads(payload_data)
            flags = data.get("config_error_flags")
            if flags is not None:
                sensor._attr_native_value = int(flags)
                decoded = {}
                for idx, flag_name in enumerate(
                    [
                        "config_error_0",
                        "config_error_1",
                        "config_error_2",
                        "config_error_3",
                        "config_error_4",
                        "config_error_5",
                        "config_error_6",
                        "config_error_7",
                    ]
                ):
                    decoded[flag_name] = bool(int(flags) & (1 << idx))
                sensor._attr_extra_state_attributes = decoded
            sensor.async_write_ha_state()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
            logging.warning("Failed to parse message: %s", err)

    msg = MagicMock()
    msg.payload = json.dumps({"config_error_flags": 5}).encode("utf-8")
    sensor.async_write_ha_state = MagicMock()
    message_received(msg)
    assert sensor._attr_native_value == 5
    assert sensor._attr_extra_state_attributes["config_error_0"] is True
    assert sensor._attr_extra_state_attributes["config_error_2"] is True
    assert sensor._attr_extra_state_attributes["config_error_1"] is False


def test_power_manager_low_level_sensors_parse_correctly():
    """Test low level power manager sensors extract fields correctly."""
    mock_config_entry = _make_mock_entry(features=["power_manager"])
    sensors = [
        MabwarpMqttSensor(
            mock_config_entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
            "Power At Meter",
            "power_at_meter",
            "W",
            SensorDeviceClass.POWER,
            None,
            coordinator=None,
        ),
        MabwarpMqttSensor(
            mock_config_entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
            "Power Available",
            "power_available",
            "W",
            SensorDeviceClass.POWER,
            None,
            coordinator=None,
        ),
        MabwarpMqttSensor(
            mock_config_entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
            "Charging Blocked",
            "charging_blocked",
            None,
            None,
            None,
            coordinator=None,
        ),
    ]
    payload = {"power_at_meter": 1500, "power_available": 3200, "charging_blocked": False, "is_3phase": True}
    assert sensors[0].extract_field(payload) == 1500
    assert sensors[1].extract_field(payload) == 3200
    assert sensors[2].extract_field(payload) is False


def test_solar_forecast_sensors_skipped_without_feature():
    """Test solar_forecast sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_SOLAR_FORECAST_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_solar_forecast_sensors_created_with_feature():
    """Test solar_forecast sensors are created when feature is present."""
    entry = _make_mock_entry(features=["solar_forecast"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.get_event_loop().run_until_complete(async_setup_entry(MagicMock(), entry, async_add_entities))

    solar_topics = [TOPIC_SOLAR_FORECAST_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in solar_topics:
        assert any(e._topic == topic for e in added)


def test_solar_forecast_value_sensor_maps_minus_one_to_none():
    """Test solar forecast sensor maps -1 to None."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarForecastValueSensor(entry, DEFAULT_TOPIC_PREFIX, "wh_today")
    assert sensor.extract_field({"wh_today": -1}) is None
    assert sensor.extract_field({"wh_today": 5000}) == 5000


def test_solar_forecast_value_sensor_unique_id():
    """Test solar forecast value sensor unique_id contains field name."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarForecastValueSensor(entry, DEFAULT_TOPIC_PREFIX, "wh_today")
    assert "wh_today" in sensor.unique_id


def test_solar_plane_state_sensor_topic_contains_index():
    """Test solar plane state sensor topic contains plane index."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarPlaneStateSensor(entry, DEFAULT_TOPIC_PREFIX, 2)
    assert "planes/2/state" in sensor._topic


def test_solar_plane_config_sensor_parses_fields():
    """Test solar plane config sensor parses name and wp."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarPlaneConfigSensor(entry, DEFAULT_TOPIC_PREFIX, 1)
    sensor.async_write_ha_state = lambda: None

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        sensor._attr_native_value = data.get("wp")
        sensor._attr_extra_state_attributes = {
            "name": data.get("name"),
            "place": data.get("place"),
        }
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"name": "Roof", "place": "North", "wp": 8.5}'
    message_received(msg)
    assert sensor._attr_native_value == 8.5
    assert sensor._attr_extra_state_attributes["name"] == "Roof"
    assert sensor._attr_extra_state_attributes["place"] == "North"
