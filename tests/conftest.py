# tests/conftest.py

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
