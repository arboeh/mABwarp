# tests/test_sensor.py

import asyncio
from unittest.mock import MagicMock, patch

from custom_components.mabwarp.sensor import async_setup_entry
from tests.conftest import make_mock_hass


def _make_mock_entry(features=None):
    from custom_components.mabwarp.const import (
        CONF_DEVICE_ID,
        CONF_FEATURES,
        CONF_TOPIC_PREFIX,
        CONF_WARP_VERSION,
        DEFAULT_TOPIC_PREFIX,
    )

    data = {
        CONF_DEVICE_ID: "TEST01",
        CONF_WARP_VERSION: "WARP3",
        CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
    }
    if features is not None:
        data[CONF_FEATURES] = features
    return type("MockEntry", (), {"data": data})()


def test_no_duplicate_unique_ids():
    """Test that no two entities have the same unique_id after async_setup_entry."""
    entry = _make_mock_entry(features=[])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    async def run_test():
        with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
            await async_setup_entry(make_mock_hass(), entry, async_add_entities)

    asyncio.run(run_test())

    unique_ids = [e.unique_id for e in added]
    assert len(unique_ids) == len(set(unique_ids)), (
        f"Duplicate unique_ids found: {[uid for uid in unique_ids if unique_ids.count(uid) > 1]}"
    )


def test_alloc_slots_have_unique_names():
    """Test that the 4 alloc slot sensors have distinct unique_ids and names."""
    entry = _make_mock_entry(features=[])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    async def run_test():
        with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
            await async_setup_entry(make_mock_hass(), entry, async_add_entities)

    asyncio.run(run_test())

    alloc_sensors = [e for e in added if "allocated_current" in e.unique_id.lower() or "alloc_" in e.unique_id.lower()]

    assert len(alloc_sensors) == 4, f"Expected 4 alloc sensors, found {len(alloc_sensors)}"

    alloc_unique_ids = [e.unique_id for e in alloc_sensors]
    assert len(alloc_unique_ids) == len(set(alloc_unique_ids)), f"Duplicate alloc unique_ids: {alloc_unique_ids}"


def test_solar_forecast_discovery_creates_background_task():
    """Test solar_forecast discovery creates async background task."""
    entry = _make_mock_entry(features=["solar_forecast"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    hass = make_mock_hass()

    async def run_test():
        with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
            with patch("custom_components.mabwarp.sensor_solar_forecast.async_subscribe", return_value=lambda: None):
                await async_setup_entry(hass, entry, async_add_entities)
        await asyncio.sleep(0)

    asyncio.run(run_test())

    assert hass.async_create_task.call_count == 1
    discovered_coro = hass.async_create_task.call_args[0][0]
    assert asyncio.iscoroutinefunction(discovered_coro) or asyncio.iscoroutine(discovered_coro)
    assert "discover_solar_planes" in discovered_coro.__name__


def test_temperature_discovery_creates_background_task():
    """Test temperature discovery creates async background task."""
    entry = _make_mock_entry(features=["temperatures"])
    added = []

    def async_add_entities(entities):
        added.extend(entities)

    hass = make_mock_hass()

    async def run_test():
        with patch("custom_components.mabwarp.sensor.async_subscribe", return_value=lambda: None):
            with patch("custom_components.mabwarp.sensor_misc.async_subscribe", return_value=lambda: None):
                await async_setup_entry(hass, entry, async_add_entities)
        await asyncio.sleep(0)

    asyncio.run(run_test())

    assert hass.async_create_task.call_count == 1
    discovered_coro = hass.async_create_task.call_args[0][0]
    assert asyncio.iscoroutinefunction(discovered_coro) or asyncio.iscoroutine(discovered_coro)
    assert "discover_temperature_keys" in discovered_coro.__name__
