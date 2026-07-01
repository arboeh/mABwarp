# tests/test_switch.py

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
)
from custom_components.mabwarp.switch import MabwarpUserEnabledSwitch


def test_switch_unique_id():
    """Test switch unique_id contains user_enabled."""
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
    switch = MabwarpUserEnabledSwitch(mock_config_entry)
    unique_id = switch.unique_id
    assert "user_enabled" in unique_id


def test_switch_initial_state():
    """Test switch initial state is off."""
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
    switch = MabwarpUserEnabledSwitch(mock_config_entry)
    assert switch._attr_is_on is False


def test_switch_icon():
    """Test switch icon is correct."""
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
    switch = MabwarpUserEnabledSwitch(mock_config_entry)
    assert switch._attr_icon == "mdi:ev-station"
