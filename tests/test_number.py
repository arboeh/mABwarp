# tests/test_number.py

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
)
from custom_components.mabwarp.number import MabwarpChargingCurrentNumber


def test_number_unique_id():
    """Test number unique_id contains charging_current_limit."""
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
    number = MabwarpChargingCurrentNumber(mock_config_entry)
    unique_id = number.unique_id
    assert "charging_current_limit" in unique_id


def test_number_limits():
    """Test number entity min, max, and step values."""
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
    number = MabwarpChargingCurrentNumber(mock_config_entry)
    assert number._attr_native_min_value == 0
    assert number._attr_native_max_value == 32
    assert number._attr_native_step == 1
    assert number._attr_native_unit_of_measurement == "A"


def test_number_initial_value():
    """Test number entity initial value is 0."""
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
    number = MabwarpChargingCurrentNumber(mock_config_entry)
    assert number._attr_native_value == 0
