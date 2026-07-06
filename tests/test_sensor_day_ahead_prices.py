# tests/test_sensor_day_ahead_prices.py

import asyncio
import json
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    TOPIC_DAY_AHEAD_PRICES_CONFIG,
    TOPIC_DAY_AHEAD_PRICES_PRICES,
    TOPIC_DAY_AHEAD_PRICES_STATE,
)
from custom_components.mabwarp.sensor import async_setup_entry
from custom_components.mabwarp.sensor_day_ahead_prices import (
    MabwarpDayAheadPriceSensor,
    MabwarpDayAheadPricesForecastSensor,
    build_day_ahead_prices_entities,
)
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


def test_day_ahead_prices_sensors_skipped_without_feature():
    """Test day_ahead_prices sensors are skipped when feature is not present."""
    entry = _make_mock_entry(features=["evse"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    for entity in added:
        topic = entity._topic
        assert TOPIC_DAY_AHEAD_PRICES_STATE.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic
        assert TOPIC_DAY_AHEAD_PRICES_PRICES.format(prefix=DEFAULT_TOPIC_PREFIX) not in topic


def test_day_ahead_prices_sensors_created_with_feature():
    """Test day_ahead_prices sensors are created when feature is present."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
        asyncio.run(async_setup_entry(make_mock_hass(), entry, async_add_entities))

    day_ahead_topics = [
        TOPIC_DAY_AHEAD_PRICES_STATE.format(prefix=DEFAULT_TOPIC_PREFIX),
        TOPIC_DAY_AHEAD_PRICES_PRICES.format(prefix=DEFAULT_TOPIC_PREFIX),
    ]
    for topic in day_ahead_topics:
        assert any(e._topic == topic for e in added)


def test_day_ahead_price_sensor_converts_current_price():
    """Test day ahead price sensor applies conversion_factor correctly."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    sensor = MabwarpDayAheadPriceSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        value = data.get("current_price")
        if value is not None and isinstance(value, (int, float)) and sensor._conversion_factor is not None:
            value = value * sensor._conversion_factor
        sensor._attr_native_value = value
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"current_price": 15000000}'
    message_received(msg)
    assert sensor._attr_native_value == 1500.0


def test_day_ahead_price_sensor_handles_null():
    """Test day ahead price sensor handles null/missing current_price."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    sensor = MabwarpDayAheadPriceSensor(entry, DEFAULT_TOPIC_PREFIX)

    assert sensor.extract_field({"current_price": None}) is None

    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            value = data.get("current_price")
            if value is not None and isinstance(value, (int, float)) and sensor._conversion_factor is not None:
                value = value * sensor._conversion_factor
            sensor._attr_native_value = value
            sensor.async_write_ha_state()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
            pass

    msg = MagicMock()
    msg.payload = b'{}'
    message_received(msg)
    assert sensor._attr_native_value is None


def test_day_ahead_price_sensor_handles_invalid_json():
    """Test day ahead price sensor handles invalid JSON gracefully."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    sensor = MabwarpDayAheadPriceSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            value = data.get("current_price")
            if value is not None and isinstance(value, (int, float)) and sensor._conversion_factor is not None:
                value = value * sensor._conversion_factor
            sensor._attr_native_value = value
            sensor.async_write_ha_state()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    msg = MagicMock()
    msg.payload = b'not json'
    message_received(msg)
    assert sensor._attr_native_value is None


def test_day_ahead_prices_forecast_sensor_parses_prices():
    """Test day ahead prices forecast sensor parses prices array correctly."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    sensor = MabwarpDayAheadPricesForecastSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        prices = data.get("prices")
        if isinstance(prices, list) and len(prices) > 0:
            first_price = prices[0]
            if isinstance(first_price, (int, float)):
                sensor._attr_native_value = first_price * 0.0001
            else:
                sensor._attr_native_value = None
        else:
            sensor._attr_native_value = None
        sensor._attr_extra_state_attributes = {
            "first_date": data.get("first_date"),
            "resolution": data.get("resolution"),
            "prices": prices if isinstance(prices, list) else [],
        }
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"first_date": 1700000000, "resolution": 15, "prices": [15000000, 16000000, 17000000]}'
    message_received(msg)
    assert sensor._attr_native_value == 1500.0
    assert sensor._attr_extra_state_attributes["first_date"] == 1700000000
    assert sensor._attr_extra_state_attributes["resolution"] == 15
    assert sensor._attr_extra_state_attributes["prices"] == [15000000, 16000000, 17000000]


def test_day_ahead_prices_forecast_sensor_handles_empty_array():
    """Test day ahead prices forecast sensor handles empty prices array."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    sensor = MabwarpDayAheadPricesForecastSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        prices = data.get("prices")
        if isinstance(prices, list) and len(prices) > 0:
            first_price = prices[0]
            if isinstance(first_price, (int, float)):
                sensor._attr_native_value = first_price * 0.0001
            else:
                sensor._attr_native_value = None
        else:
            sensor._attr_native_value = None
        sensor._attr_extra_state_attributes = {
            "first_date": data.get("first_date"),
            "resolution": data.get("resolution"),
            "prices": prices if isinstance(prices, list) else [],
        }
        sensor.async_write_ha_state()

    msg = MagicMock()
    msg.payload = b'{"first_date": 1700000000, "resolution": 15, "prices": []}'
    message_received(msg)
    assert sensor._attr_native_value is None
    assert sensor._attr_extra_state_attributes["prices"] == []


def test_day_ahead_prices_forecast_sensor_handles_invalid_json():
    """Test day ahead prices forecast sensor handles invalid JSON gracefully."""
    entry = _make_mock_entry(features=["day_ahead_prices"])
    sensor = MabwarpDayAheadPricesForecastSensor(entry, DEFAULT_TOPIC_PREFIX)
    sensor.async_write_ha_state = MagicMock()

    def message_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            prices = data.get("prices")
            if isinstance(prices, list) and len(prices) > 0:
                first_price = prices[0]
                if isinstance(first_price, (int, float)):
                    sensor._attr_native_value = first_price * 0.0001
                else:
                    sensor._attr_native_value = None
            else:
                sensor._attr_native_value = None
            sensor._attr_extra_state_attributes = {
                "first_date": data.get("first_date"),
                "resolution": data.get("resolution"),
                "prices": prices if isinstance(prices, list) else [],
            }
            sensor.async_write_ha_state()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    msg = MagicMock()
    msg.payload = b'not json'
    message_received(msg)
    assert sensor._attr_native_value is None
