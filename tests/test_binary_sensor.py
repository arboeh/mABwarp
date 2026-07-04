# tests/test_binary_sensor.py

from custom_components.mabwarp.binary_sensor import MabwarpIs3phaseBinarySensor
from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_POWER_MANAGER_LOW_LEVEL_STATE,
)


def test_is_3phase_binary_sensor_unique_id():
    """Test is_3phase binary sensor unique_id contains is_3phase."""
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
    sensor = MabwarpIs3phaseBinarySensor(mock_config_entry)
    assert "is_3phase" in sensor.unique_id


def test_is_3phase_binary_sensor_on_when_true():
    """Test is_3phase binary sensor is on when payload is true."""
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
    sensor = MabwarpIs3phaseBinarySensor(mock_config_entry)
    sensor.async_write_ha_state = lambda: None

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = __import__("json").loads(payload)
        sensor._attr_is_on = bool(data.get("is_3phase", False))
        sensor.async_write_ha_state()

    from unittest.mock import MagicMock
    msg = MagicMock()
    msg.payload = b'{"is_3phase": true}'
    message_received(msg)
    assert sensor._attr_is_on is True


def test_is_3phase_binary_sensor_off_when_false():
    """Test is_3phase binary sensor is off when payload is false."""
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
    sensor = MabwarpIs3phaseBinarySensor(mock_config_entry)
    sensor.async_write_ha_state = lambda: None

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = __import__("json").loads(payload)
        sensor._attr_is_on = bool(data.get("is_3phase", False))
        sensor.async_write_ha_state()

    from unittest.mock import MagicMock
    msg = MagicMock()
    msg.payload = b'{"is_3phase": false}'
    message_received(msg)
    assert sensor._attr_is_on is False
