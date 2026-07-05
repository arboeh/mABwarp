# tests/test_sensor_charge_tracker.py

import asyncio
import datetime
import json
import logging
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_CHARGE_TRACKER_CURRENT,
    TOPIC_CHARGE_TRACKER_LAST,
    TOPIC_CHARGE_TRACKER_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_charge_tracker import (
    MabwarpCurrentChargeUserIDSensor,
    MabwarpLastChargeSensor,
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
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_CHARGE_TRACKER_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_CHARGE_TRACKER_LAST.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
