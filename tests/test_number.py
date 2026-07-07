# tests/test_number.py

import asyncio
import logging
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
)
from custom_components.mabwarp.number import (
    MabwarpChargeLimitsDurationNumber,
    MabwarpChargeLimitsEnergyNumber,
    MabwarpChargingCurrentNumber,
)


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


def test_charge_limits_duration_number_unique_id():
    """Test charge limits duration number unique_id."""
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
    number = MabwarpChargeLimitsDurationNumber(mock_config_entry)
    assert "charge_limits_duration" in number.unique_id


def test_charge_limits_duration_number_limits():
    """Test charge limits duration number limits."""
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
    number = MabwarpChargeLimitsDurationNumber(mock_config_entry)
    assert number._attr_native_min_value == 0
    assert number._attr_native_max_value == 24
    assert number._attr_native_step == 0.5
    assert number._attr_native_unit_of_measurement == "h"


def test_charge_limits_energy_number_unique_id():
    """Test charge limits energy number unique_id."""
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
    number = MabwarpChargeLimitsEnergyNumber(mock_config_entry)
    assert "charge_limits_energy_wh" in number.unique_id


def test_charge_limits_energy_number_limits():
    """Test charge limits energy number limits."""
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
    number = MabwarpChargeLimitsEnergyNumber(mock_config_entry)
    assert number._attr_native_min_value == 0
    assert number._attr_native_max_value == 100000
    assert number._attr_native_step == 100
    assert number._attr_native_unit_of_measurement == "Wh"


def test_charging_current_number_unavailable_after_three_parse_errors(caplog):
    """Test number entity becomes unavailable after 3 consecutive parse errors."""
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
    number.hass = MagicMock()
    number.hass.loop = MagicMock()
    number.async_write_ha_state = MagicMock()

    captured_callback = None

    async def mock_async_subscribe(hass, topic, callback, qos):
        nonlocal captured_callback
        captured_callback = callback
        return lambda: None

    with patch(
        "custom_components.mabwarp.number.async_subscribe",
        side_effect=mock_async_subscribe,
    ):
        asyncio.run(number.async_added_to_hass())

    assert captured_callback is not None
    with caplog.at_level(logging.WARNING, logger="custom_components.mabwarp.entity_base"):
        for _ in range(3):
            msg = MagicMock()
            msg.payload = b"not json"
            captured_callback(msg)

    assert number._attr_available is False
    assert "Failed to parse MQTT message" in caplog.text
