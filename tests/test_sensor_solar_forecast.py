# tests/test_sensor_solar_forecast.py

import asyncio
import json
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_SOLAR_FORECAST_PLANES_CONFIG,
    TOPIC_SOLAR_FORECAST_PLANES_STATE,
    TOPIC_SOLAR_FORECAST_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_solar_forecast import (
    MabwarpSolarForecastValueSensor,
    MabwarpSolarPlaneConfigSensor,
    MabwarpSolarPlaneStateSensor,
)


def _make_mock_hass():
    hass = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[])
    hass.async_create_task = MagicMock()
    return hass


def _make_mock_entry(features=None):
    data = {
        CONF_DEVICE_ID: "TEST01",
        CONF_WARP_VERSION: "WARP3",
        CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
    }
    if features is not None:
        data[CONF_FEATURES] = features
    return type("MockEntry", (), {"data": data})()


def test_solar_forecast_sensors_skipped_without_feature():
    """Test solar_forecast sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(_make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_SOLAR_FORECAST_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_solar_forecast_sensors_created_with_feature():
    """Test solar_forecast sensors are created when feature is present."""
    entry = _make_mock_entry(features=["solar_forecast"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(_make_mock_hass(), entry, async_add_entities))

    solar_topics = [TOPIC_SOLAR_FORECAST_STATE.format(prefix=DEFAULT_TOPIC_PREFIX)]
    for topic in solar_topics:
        assert any(e._topic == topic for e in added)


def test_solar_forecast_value_sensor_maps_minus_one_to_none():
    """Test solar forecast sensor maps -1 to None."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarForecastValueSensor(entry, DEFAULT_TOPIC_PREFIX, "wh_today")
    assert sensor.extract_field({"wh_today": -1}) is None
    assert sensor.extract_field({"wh_today": 5000}) == 5000


def test_solar_forecast_value_sensor_unique_id():
    """Test solar forecast value sensor unique_id contains field name."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarForecastValueSensor(entry, DEFAULT_TOPIC_PREFIX, "wh_today")
    assert "wh_today" in sensor.unique_id


def test_solar_plane_state_sensor_topic_contains_index():
    """Test solar plane state sensor topic contains plane index."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarPlaneStateSensor(entry, DEFAULT_TOPIC_PREFIX, 2)
    assert "planes/2/state" in sensor._topic


def test_solar_plane_config_sensor_parses_fields():
    """Test solar plane config sensor parses name and wp."""
    entry = _make_mock_entry(features=["solar_forecast"])
    sensor = MabwarpSolarPlaneConfigSensor(entry, DEFAULT_TOPIC_PREFIX, 1)
    sensor.async_write_ha_state = lambda: None

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        sensor._attr_native_value = data.get("wp")
        sensor._attr_extra_state_attributes = {
            "name": data.get("name"),
            "place": data.get("place"),
        }
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"name": "Roof", "place": "North", "wp": 8.5}'
    message_received(msg)
    assert sensor._attr_native_value == 8.5
    assert sensor._attr_extra_state_attributes["name"] == "Roof"
    assert sensor._attr_extra_state_attributes["place"] == "North"
