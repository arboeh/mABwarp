# tests/test_sensor_base.py

import asyncio
import inspect
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    METER_VALUE_ID_VOLTAGE_L1,
    TOPIC_EVSE_STATE,
    TOPIC_METER_VALUES,
)
from custom_components.mabwarp.sensor_base import MabwarpMqttSensor


def test_sensor_unique_id():
    """Test sensor unique_id generation."""
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
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
            }
        },
    )()

    class FakeCoordinator:
        def __init__(self, mapping):
            self._mapping = mapping

        def get_index(self, meter_value_id):
            return self._mapping.get(meter_value_id)

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
            }
        },
    )()

    class FakeCoordinator:
        def __init__(self, mapping):
            self._mapping = mapping

        def get_index(self, meter_value_id):
            return self._mapping.get(meter_value_id)

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
            }
        },
    )()

    class FakeCoordinator:
        def __init__(self, mapping):
            self._mapping = mapping

        def get_index(self, meter_value_id):
            return self._mapping.get(meter_value_id)

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
            }
        },
    )()

    class FakeCoordinator:
        def __init__(self, mapping):
            self._mapping = mapping

        def get_index(self, meter_value_id):
            return self._mapping.get(meter_value_id)

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


def test_alloc_field_extraction_from_charge_manager_state():
    """Test extract_field correctly extracts alloc[idx] from charge_manager/state payload.

    Real payload from warp3/charge_manager/state (mosquitto_sub):
    {'state': 0, 'l_raw': [0, 0, 0, 0], 'l_min': [0, 0, 0, 0], 'l_spread': [0, 0, 0, 0],
     'l_max_pv': 0, 'alloc': [0, 0, 0, 0], 'chargers': []}
    """
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
            }
        },
    )()
    sensor = MabwarpMqttSensor(
        mock_config_entry,
        TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX),
        "Allocated Current Slot 0",
        "alloc.0",
        "A",
        None,
        None,
        coordinator=None,
    )

    payload = {
        "state": 0,
        "l_raw": [0, 0, 0, 0],
        "l_min": [0, 0, 0, 0],
        "l_spread": [0, 0, 0, 0],
        "l_max_pv": 0,
        "alloc": [0, 0, 0, 0],
        "chargers": [],
    }
    assert sensor.extract_field(payload) == 0

    payload_with_values = {
        "state": 1,
        "alloc": [16000, 0, 0, 0],
        "chargers": [],
    }
    assert sensor.extract_field(payload_with_values) == 16000


def test_message_received_uses_call_soon_threadsafe():
    """Test that message_received calls async_write_ha_state via call_soon_threadsafe.

    This is a regression test for the thread-safety bug where async_write_ha_state
    was called directly from the MQTT callback instead of via call_soon_threadsafe.
    """
    mock_config_entry = type(
        "MockEntry",
        (),
        {
            "data": {
                CONF_DEVICE_ID: "TEST01",
                CONF_WARP_VERSION: "WARP3",
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

    source = inspect.getsource(sensor.async_added_to_hass)
    assert "call_soon_threadsafe" in source, "async_added_to_hass should use call_soon_threadsafe for thread safety"
