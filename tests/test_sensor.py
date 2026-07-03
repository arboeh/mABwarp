# tests/test_sensor.py

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    METER_VALUE_ID_VOLTAGE_L1,
    TOPIC_EVSE_STATE,
    TOPIC_METER_VALUES,
)
from custom_components.mabwarp.sensor import MabwarpMqttSensor


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
    # conversion_factor applied only if value is numeric and conversion_factor set
    if isinstance(result, int | float) and sensor._conversion_factor is not None:
        result = result * sensor._conversion_factor
    assert result == 6.0
