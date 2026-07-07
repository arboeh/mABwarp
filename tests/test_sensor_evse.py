# tests/test_sensor_evse.py

import asyncio
from unittest.mock import MagicMock, patch

from homeassistant.helpers.entity import EntityCategory

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_METER_VALUES,
    TOPIC_NFC_LAST_TAG,
)
from custom_components.mabwarp.sensor import async_setup_entry
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


def test_meter_sensors_skipped_without_meters_feature():
    """Test meter sensors are skipped when features=['evse']."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_meter_sensors_created_with_empty_features_fallback():
    """Test meter sensors are created when features is empty (fallback)."""
    entry = _make_mock_entry(features=[])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    meter_topics = [e._topic for e in added if TOPIC_METER_VALUES.format(prefix=DEFAULT_TOPIC_PREFIX) in e._topic]
    assert len(meter_topics) > 0


def test_nfc_sensors_skipped_without_nfc_feature():
    """Test NFC sensors are skipped when features=['evse']."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_NFC_LAST_TAG.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_nfc_last_tag_sensor_disabled_by_default():
    """Test NFC Last Tag sensor is disabled by default and marked diagnostic."""
    entry = _make_mock_entry(features=["nfc"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    nfc_tag_sensors = [e for e in added if getattr(e, "_attr_translation_key", None) == "nfc_last_tag"]
    assert len(nfc_tag_sensors) == 1
    assert nfc_tag_sensors[0].entity_registry_enabled_default is False
    assert nfc_tag_sensors[0].entity_category == EntityCategory.DIAGNOSTIC
