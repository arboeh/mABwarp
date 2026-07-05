# tests/test_sensor_charge_limits.py

import asyncio
import datetime
import json
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_CHARGE_LIMITS_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_charge_limits import (
    MabwarpChargeLimitsEnergySensor,
    MabwarpChargeLimitsTimestampSensor,
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


def test_charge_limits_sensors_skipped_without_feature():
    """Test charge_limits sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_CHARGE_LIMITS_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_charge_limits_sensors_created_with_feature():
    """Test charge_limits sensors are created when feature is present."""
    entry = _make_mock_entry(features=["charge_limits"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    charge_limits_topics = [TOPIC_CHARGE_LIMITS_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in charge_limits_topics:
        assert any(e._topic == topic for e in added)


def test_charge_limits_timestamp_sensor_converts_ms_to_datetime():
    """Test charge limits timestamp sensor converts ms to datetime."""
    entry = _make_mock_entry(features=["charge_limits"])
    sensor = MabwarpChargeLimitsTimestampSensor(entry, DEFAULT_TOPIC_PREFIX, "Start", "start_timestamp_ms")
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        value = data.get("start_timestamp_ms")
        if value is not None:
            sensor._attr_native_value = datetime.datetime.fromtimestamp(int(value) / 1000, tz=datetime.UTC)
        else:
            sensor._attr_native_value = None
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"start_timestamp_ms": 1700000000000}'
    message_received(msg)
    assert sensor._attr_native_value is not None
    assert sensor._attr_native_value.year == 2023


def test_charge_limits_energy_sensor_handles_null():
    """Test charge limits energy sensor handles null values."""
    entry = _make_mock_entry(features=["charge_limits"])
    sensor = MabwarpChargeLimitsEnergySensor(entry, DEFAULT_TOPIC_PREFIX, "Start Energy", "start_energy_kwh", "kWh")
    assert sensor.extract_field({"start_energy_kwh": None}) is None
    assert sensor.extract_field({"start_energy_kwh": 12.5}) == 12.5
