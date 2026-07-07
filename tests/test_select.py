# tests/test_select.py

import asyncio
import logging
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
)
from custom_components.mabwarp.select import MabwarpChargeModeSelect


def test_charge_mode_select_unique_id():
    """Test charge mode select unique_id contains charge_mode."""
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
    select = MabwarpChargeModeSelect(mock_config_entry)
    assert "charge_mode" in select.unique_id


def test_charge_mode_select_options():
    """Test charge mode select options match CHARGE_MODE_MAP."""
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
    select = MabwarpChargeModeSelect(mock_config_entry)
    assert set(select._attr_options) == {
        "Schnell",
        "Aus",
        "PV",
        "Min+PV",
        "Min",
        "Eco",
        "Eco+PV",
        "Eco+Min",
        "Eco+Min+PV",
    }


def test_charge_mode_select_current_option_from_payload():
    """Test charge mode select parses current option from payload."""
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
    select = MabwarpChargeModeSelect(mock_config_entry)
    select.async_write_ha_state = lambda: None

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = __import__("json").loads(payload)
        mode = data.get("mode")
        if mode is not None:
            from custom_components.mabwarp.const import CHARGE_MODE_MAP

            select._attr_current_option = CHARGE_MODE_MAP.get(int(mode), f"Unknown ({mode})")

    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.payload = b'{"mode": 2}'
    message_received(msg)
    assert select._attr_current_option == "PV"


def test_charge_mode_select_unavailable_after_three_parse_errors(caplog):
    """Test select entity becomes unavailable after 3 consecutive parse errors."""
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
    select = MabwarpChargeModeSelect(mock_config_entry)
    select.hass = MagicMock()
    select.hass.loop = MagicMock()
    select.async_write_ha_state = MagicMock()

    captured_callback = None

    async def mock_async_subscribe(hass, topic, callback, qos):
        nonlocal captured_callback
        captured_callback = callback
        return lambda: None

    with patch(
        "custom_components.mabwarp.select.async_subscribe",
        side_effect=mock_async_subscribe,
    ):
        asyncio.run(select.async_added_to_hass())

    assert captured_callback is not None
    with caplog.at_level(logging.WARNING, logger="custom_components.mabwarp.entity_base"):
        for _ in range(3):
            msg = MagicMock()
            msg.payload = b"not json"
            captured_callback(msg)

    assert select._attr_available is False
    assert "Failed to parse MQTT message" in caplog.text
