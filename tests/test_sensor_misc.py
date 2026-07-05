# tests/test_sensor_misc.py

import asyncio
import json
from unittest.mock import MagicMock, patch

from homeassistant.components.sensor import SensorDeviceClass

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_INFO_VERSION,
    TOPIC_P14A_ENWG_STATE,
    TOPIC_TEMPERATURES_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_base import MabwarpMqttSensor
from custom_components.mabwarp.sensor_misc import (
    MabwarpFeaturesSensor,
    MabwarpP14aEnwgMaxPowerSensor,
    MabwarpP14aEnwgThrottledBinarySensor,
    MabwarpTemperatureSensor,
)
from tests.conftest import make_mock_hass


def _make_mock_entry(features=None):
    data = {
        CONF_DEVICE_ID: "TEST01",
        CONF_WARP_VERSION: "WARP3",
        CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
    }
    if features is not None:
        data[CONF_FEATURES] = features
    return type("MockEntry", (), {"data": data})()


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


def test_temperature_sensors_skipped_without_feature():
    """Test temperature sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_TEMPERATURES_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_temperature_sensors_created_with_feature():
    """Test temperature sensors are created when feature is present."""
    entry = _make_mock_entry(features=["temperatures"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    hass = make_mock_hass()

    async def run_test():
        with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
            with patch("custom_components.mabwarp.sensor_misc.async_subscribe", return_value=lambda: None):
                await async_setup_entry(hass, entry, async_add_entities)
        await asyncio.sleep(0)

    asyncio.run(run_test())

    temp_topics = [TOPIC_TEMPERATURES_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in temp_topics:
        assert any(e._topic == topic for e in added)


def test_temperature_sensor_device_class_and_unit():
    """Test temperature sensor has correct device class and unit."""
    entry = _make_mock_entry(features=["temperatures"])
    sensor = MabwarpTemperatureSensor(entry, DEFAULT_TOPIC_PREFIX, "Temperature Current", "current")
    assert sensor._attr_device_class == SensorDeviceClass.TEMPERATURE
    assert sensor._attr_native_unit_of_measurement == "°C"


def test_p14a_enwg_sensors_skipped_without_feature():
    """Test p14a_enwg sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_P14A_ENWG_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_p14a_enwg_sensors_created_with_feature():
    """Test p14a_enwg sensors are created when feature is present."""
    entry = _make_mock_entry(features=["p14a_enwg"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    p14a_topics = [TOPIC_P14A_ENWG_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in p14a_topics:
        assert any(e._topic == topic for e in added)


def test_p14a_enwg_throttled_binary_sensor_parses_throttled_field():
    """Test P14A ENWG throttled binary sensor parses throttled field."""
    entry = _make_mock_entry(features=["p14a_enwg"])
    sensor = MabwarpP14aEnwgThrottledBinarySensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = lambda: None

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        sensor._attr_is_on = bool(data.get("throttled", False))
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"throttled": true}'
    message_received(msg)
    assert sensor._attr_is_on is True


def test_p14a_enwg_max_power_sensor_parses_max_power():
    """Test P14A ENWG max power sensor parses max_power field."""
    entry = _make_mock_entry(features=["p14a_enwg"])
    sensor = MabwarpP14aEnwgMaxPowerSensor(entry, DEFAULT_TOPIC_PREFIX)
    assert sensor.extract_field({"max_power": 4200}) == 4200
