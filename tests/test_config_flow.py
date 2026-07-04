# tests/test_config_flow.py

import asyncio
from unittest.mock import MagicMock, patch


class MockConfigEntry:
    """Minimal mock config entry."""

    def __init__(self, domain, data, title):
        self.domain = domain
        self.data = data
        self.title = title


from homeassistant.data_entry_flow import FlowResultType

from custom_components.mabwarp.config_flow import MabwarpConfigFlow
from custom_components.mabwarp.const import CONF_DEVICE_ID


def _make_mock_hass(has_mqtt=True, existing_entries=None):
    """Create a minimal mock hass object."""
    hass = MagicMock()
    hass.services.has_service.return_value = has_mqtt

    config_entries = MagicMock()
    config_entries._entries = existing_entries or []
    config_entries.async_entries = MagicMock(return_value=existing_entries or [])
    hass.config_entries = config_entries

    return hass


def test_form_shows_correctly():
    """Test that the form is shown correctly."""
    hass = _make_mock_hass()
    flow = MabwarpConfigFlow()
    flow.hass = hass
    result = asyncio.get_event_loop().run_until_complete(flow.async_step_user(None))
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


def test_empty_device_id_uses_topic_prefix():
    """Test that empty device_id uses topic_prefix as fallback."""
    hass = _make_mock_hass(has_mqtt=True)
    flow = MabwarpConfigFlow()
    flow.hass = hass
    result = asyncio.get_event_loop().run_until_complete(
        flow.async_step_user({"topic_prefix": "warp3", "device_id": "", "warp_version": "WARP3"})
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "WARP Charger (warp3)"
    assert result["data"][CONF_DEVICE_ID] == "warp3"


def test_successful_entry_creation():
    """Test successful config entry creation."""
    hass = _make_mock_hass(has_mqtt=True)
    flow = MabwarpConfigFlow()
    flow.hass = hass
    result = asyncio.get_event_loop().run_until_complete(
        flow.async_step_user({"topic_prefix": "warp", "device_id": "TEST01", "warp_version": "WARP3"})
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "WARP Charger (TEST01)"
    assert result["data"][CONF_DEVICE_ID] == "TEST01"


def test_mqtt_not_available_aborts():
    """Test that flow aborts when MQTT is not available."""
    hass = _make_mock_hass(has_mqtt=False)
    flow = MabwarpConfigFlow()
    flow.hass = hass
    result = asyncio.get_event_loop().run_until_complete(
        flow.async_step_user({"topic_prefix": "warp", "device_id": "TEST01", "warp_version": "WARP3"})
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "mqtt_not_available"


def test_duplicate_device_id_aborts():
    """Test that flow aborts on duplicate device_id."""
    existing_entry = MockConfigEntry(
        domain="mabwarp",
        data={"device_id": "TEST01"},
        title="WARP Charger (TEST01)",
    )
    hass = _make_mock_hass(has_mqtt=True, existing_entries=[existing_entry])
    flow = MabwarpConfigFlow()
    flow.hass = hass
    result = asyncio.get_event_loop().run_until_complete(
        flow.async_step_user({"topic_prefix": "warp", "device_id": "TEST01", "warp_version": "WARP3"})
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


def _mock_msg(payload_bytes):
    """Create a mock MQTT message."""
    msg = MagicMock()
    msg.payload = payload_bytes
    return msg


def test_features_detected_and_stored():
    """Test that detected features are stored in entry data."""
    hass = _make_mock_hass(has_mqtt=True)
    flow = MabwarpConfigFlow()
    flow.hass = hass

    callback_holder = {}

    def mock_async_subscribe(hass, topic, callback, qos):
        callback_holder["callback"] = callback
        return lambda: None

    with patch("custom_components.mabwarp.config_flow.async_subscribe", side_effect=mock_async_subscribe):
        result = asyncio.get_event_loop().run_until_complete(
            flow.async_step_user({"topic_prefix": "warp", "device_id": "TEST01", "warp_version": "WARP3"})
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["features"] == ["evse", "meters", "nfc"]


def test_features_timeout_falls_back_to_empty_list():
    """Test that feature timeout falls back to empty list and still creates entry."""
    hass = _make_mock_hass(has_mqtt=True)
    flow = MabwarpConfigFlow()
    flow.hass = hass

    def mock_async_subscribe(hass, topic, callback, qos):
        return lambda: None

    with patch("custom_components.mabwarp.config_flow.async_subscribe", side_effect=mock_async_subscribe):
        result = asyncio.get_event_loop().run_until_complete(
            flow.async_step_user({"topic_prefix": "warp", "device_id": "TEST01", "warp_version": "WARP3"})
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["features"] == []
