# tests/conftest.py

import asyncio
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry  # type: ignore

from custom_components.mabwarp.const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
            CONF_DEVICE_ID: "TEST01",
            CONF_WARP_VERSION: "WARP3",
        },
        title="WARP Charger (TEST01)",
    )


def make_mock_hass():
    """Return a MagicMock hass with async_create_task that actually schedules coroutines."""
    hass = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[])
    create_task_mock = MagicMock(side_effect=lambda coro: asyncio.get_event_loop().create_task(coro))
    hass.async_create_task = create_task_mock
    hass.async_subscribe = MagicMock(return_value=lambda: None)
    return hass
