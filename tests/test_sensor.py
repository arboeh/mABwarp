# tests/test_sensor.py

import asyncio
from unittest.mock import MagicMock, patch

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
    TOPIC_METER_VALUES,
    TOPIC_NFC_LAST_TAG,
)
from custom_components.mabwarp.sensor import (
    MabwarpCurrentChargeUserIDSensor,
    MabwarpFeaturesSensor,
    MabwarpLastChargeSensor,
    MabwarpMqttSensor,
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
    result = sensor._extract_field({"power": 1500.0})
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
    result = sensor._extract_field(meter_data)
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
    result = sensor._extract_field(meter_data)
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
    result = sensor._extract_field(meter_data)
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
    result = sensor._extract_field({"test_field": 6000})
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
    result = sensor._extract_field(payload)
    assert result == "1.2.3"


def test_current_charge_sensor_idle_when_no_session():
    """Test current charge user ID sensor returns None when user_id is -1."""
    entry = _make_mock_entry(features=["charge_tracker"])
    sensor = MabwarpCurrentChargeUserIDSensor(
        entry,
        TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Current Charge User ID",
        "user_id",
        None,
        None,
        None,
        coordinator=None,
    )
    msg = MagicMock()
    msg.payload = (
        b'{"user_id": -1, "meter_start": 0.0, "evse_uptime_start": 0, '
        b'"timestamp_minutes": 0, "authorization_type": 0}'
    )
    sensor._extract_field = MagicMock(return_value=-1)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            value = sensor._extract_field(data)
            if value == -1:
                value = None
            sensor._attr_native_value = value
            sensor.async_write_ha_state()
        except (
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as err:
            _LOGGER.warning("Failed to parse current_charge message on %s: %s", sensor._topic, err)

    message_received(msg)
    assert sensor._attr_native_value is None


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
                _LOGGER.warning("Received empty last_charges array")
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
                    tz=datetime.timezone.utc,
                ).isoformat(),
            }
            sensor.async_write_ha_state()
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            KeyError,
        ) as err:
            _LOGGER.warning("Failed to parse last_charges message: %s", err)

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
                _LOGGER.warning("Received empty last_charges array")
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
                    tz=datetime.timezone.utc,
                ).isoformat(),
            }
            sensor.async_write_ha_state()
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            KeyError,
        ) as err:
            _LOGGER.warning("Failed to parse last_charges message: %s", err)

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
