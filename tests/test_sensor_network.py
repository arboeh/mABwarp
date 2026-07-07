# tests/test_sensor_network.py

import asyncio
import json
from unittest.mock import MagicMock, patch

from homeassistant.helpers.entity import EntityCategory

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_ETHERNET_STATE,
    TOPIC_WIFI_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_network import (
    MabwarpEthernetIpAddressSensor,
    MabwarpEthernetLinkSpeedSensor,
    MabwarpWifiConnectionStateSensor,
    MabwarpWifiIpAddressSensor,
    MabwarpWifiSignalStrengthSensor,
    build_network_entities,
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


def test_wifi_sensors_always_created():
    """Test WiFi sensors are always created regardless of features."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    wifi_topics = [TOPIC_WIFI_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in wifi_topics:
        assert any(e._topic == topic for e in added)


def test_ethernet_sensors_created_with_feature():
    """Test ethernet sensors are created when feature is present."""
    entry = _make_mock_entry(features=["ethernet"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    ethernet_topics = [TOPIC_ETHERNET_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in ethernet_topics:
        assert any(e._topic == topic for e in added)


def test_ethernet_sensors_created_with_empty_features():
    """Test ethernet sensors are created when features list is empty."""
    entry = _make_mock_entry(features=[])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    ethernet_topics = [TOPIC_ETHERNET_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in ethernet_topics:
        assert any(e._topic == topic for e in added)


def test_ethernet_sensors_skipped_without_feature():
    """Test ethernet sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse", "meters"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_ETHERNET_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_wifi_signal_strength_sensor_parses_rssi():
    """Test WiFi signal strength sensor parses sta_rssi correctly."""
    entry = _make_mock_entry()
    sensor = MabwarpWifiSignalStrengthSensor(entry, DEFAULT_TOPIC_PREFIX)
    payload = {"sta_rssi": -65}
    result = sensor.extract_field(payload)
    assert result == -65


def test_wifi_signal_strength_sensor_handles_null():
    """Test WiFi signal strength sensor handles null/missing sta_rssi."""
    entry = _make_mock_entry()
    sensor = MabwarpWifiSignalStrengthSensor(entry, DEFAULT_TOPIC_PREFIX)
    assert sensor.extract_field({"sta_rssi": None}) is None

    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            value = data.get("sta_rssi")
            if value is not None and sensor._conversion_factor is not None:
                value = value * sensor._conversion_factor
            sensor._attr_native_value = value
            sensor.async_write_ha_state()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    msg = MagicMock()
    msg.payload = b"{}"
    message_received(msg)
    assert sensor._attr_native_value is None


def test_network_sensors_have_diagnostic_entity_category():
    """Test all network sensors are marked as diagnostic entities."""
    entry = _make_mock_entry(features=[])
    sensors = build_network_entities(entry, DEFAULT_TOPIC_PREFIX, [])
    for sensor in sensors:
        assert sensor.entity_category == EntityCategory.DIAGNOSTIC
