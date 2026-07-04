# tests/test_select.py

from custom_components.mabwarp.select import MabwarpChargeModeSelect
from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
)


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
    assert set(select._attr_options) == {"Standby", "Min", "PV", "Min+PV"}


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
            select._attr_current_option = CHARGE_MODE_MAP.get(int(mode))

    from unittest.mock import MagicMock
    msg = MagicMock()
    msg.payload = b'{"mode": 2}'
    message_received(msg)
    assert select._attr_current_option == "PV"
