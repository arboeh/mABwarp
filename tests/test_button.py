# tests/test_button.py

from custom_components.mabwarp.button import MabwarpButtonBase
from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_CHARGE_LIMITS_RESTART,
    TOPIC_EVSE_START,
    TOPIC_EVSE_STOP,
)


def test_start_button_unique_id():
    """Test start button unique_id contains start_charging."""
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
    button = MabwarpButtonBase(
        mock_config_entry,
        "Start Charging",
        TOPIC_EVSE_START.format(prefix=DEFAULT_TOPIC_PREFIX),
        "mdi:play-circle",
    )
    assert "start_charging" in button.unique_id


def test_stop_button_unique_id():
    """Test stop button unique_id contains stop_charging."""
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
    button = MabwarpButtonBase(
        mock_config_entry,
        "Stop Charging",
        TOPIC_EVSE_STOP.format(prefix=DEFAULT_TOPIC_PREFIX),
        "mdi:stop-circle",
    )
    assert "stop_charging" in button.unique_id


def test_button_icons():
    """Test button icons are correct."""
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
    start_button = MabwarpButtonBase(
        mock_config_entry,
        "Start Charging",
        TOPIC_EVSE_START.format(prefix=DEFAULT_TOPIC_PREFIX),
        "mdi:play-circle",
    )
    stop_button = MabwarpButtonBase(
        mock_config_entry,
        "Stop Charging",
        TOPIC_EVSE_STOP.format(prefix=DEFAULT_TOPIC_PREFIX),
        "mdi:stop-circle",
    )
    assert start_button._attr_icon == "mdi:play-circle"
    assert stop_button._attr_icon == "mdi:stop-circle"


def test_restart_charge_limits_button_unique_id():
    """Test restart charge limits button unique_id contains charge_limits_restart."""
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
    button = MabwarpButtonBase(
        mock_config_entry,
        "Restart Charge Limits",
        TOPIC_CHARGE_LIMITS_RESTART.format(prefix=DEFAULT_TOPIC_PREFIX),
        "mdi:restart",
    )
    assert "charge_limits_restart" in button.unique_id
