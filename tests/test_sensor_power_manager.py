# tests/test_sensor_power_manager.py

import asyncio
import json
import logging
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
    TOPIC_POWER_MANAGER_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_base import MabwarpMqttSensor
from custom_components.mabwarp.sensor_power_manager import (
    MabwarpChargeModeSensor,
    MabwarpConfigErrorFlagsSensor,
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


def test_power_manager_sensors_skipped_without_feature():
    """Test power_manager sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

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
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

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
    assert sensor._attr_native_value == "Schnell"

    msg.payload = b'{"mode": 1}'
    message_received(msg)
    assert sensor._attr_native_value == "Aus"

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
            None,
            None,
            coordinator=None,
        ),
        MabwarpMqttSensor(
            mock_config_entry,
            TOPIC_POWER_MANAGER_LOW_LEVEL_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
            "Power Available",
            "power_available",
            "W",
            None,
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


def test_config_error_flags_sensor_unavailable_after_three_parse_errors(caplog):
    """Test config error flags sensor becomes unavailable after 3 consecutive parse errors."""
    entry = _make_mock_entry(features=["power_manager"])
    sensor = MabwarpConfigErrorFlagsSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.hass = MagicMock()
    sensor.hass.loop = MagicMock()
    sensor.async_write_ha_state = MagicMock()

    captured_callback = None

    async def mock_async_subscribe(hass, topic, callback, qos):
        nonlocal captured_callback
        captured_callback = callback
        return lambda: None

    with patch(
        "custom_components.mabwarp.sensor_power_manager.async_subscribe",
        side_effect=mock_async_subscribe,
    ):
        asyncio.run(sensor.async_added_to_hass())

    assert captured_callback is not None
    with caplog.at_level(logging.WARNING, logger="custom_components.mabwarp.entity_base"):
        for _ in range(3):
            msg = MagicMock()
            msg.payload = b"not json"
            captured_callback(msg)

    assert sensor._attr_available is False
    assert "Failed to parse MQTT message" in caplog.text
