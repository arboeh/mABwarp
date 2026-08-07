# tests/conftest.py

import asyncio
import logging
import sys
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

logging.getLogger("asyncio").setLevel(logging.WARNING)


def pytest_configure(config):
    """Re-enable sockets blocked by pytest-homeassistant-custom-component.

    The HA test plugin calls pytest_socket.disable_socket() for every test,
    which breaks Windows event loop creation (ProactorEventLoop needs
    socket.socketpair()). Monkeypatching disable_socket is the only viable
    workaround because pytest_runtest_setup hooks from conftest.py run before
    plugin hooks.
    """
    if "pytest_socket" in sys.modules:
        import pytest_socket

        pytest_socket.disable_socket = lambda *args, **kwargs: None


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

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    create_task_mock = MagicMock(side_effect=lambda coro: loop.create_task(coro))
    hass.async_create_task = create_task_mock
    hass.async_subscribe = MagicMock(return_value=lambda: None)
    return hass
