# custom_components/mabwarp/config_flow.py

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    WARP_VERSIONS,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): str,
        vol.Optional(CONF_DEVICE_ID, default=""): str,
        vol.Optional(CONF_WARP_VERSION, default="WARP3"): vol.In(WARP_VERSIONS),
    }
)


class MabwarpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Configuration flow for mABwarp."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if not self.hass.services.has_service("mqtt", "publish"):
                return self.async_abort(reason="mqtt_not_available")

            if not user_input.get(CONF_DEVICE_ID):
                user_input[CONF_DEVICE_ID] = user_input[CONF_TOPIC_PREFIX]

            existing = [
                e for e in self._async_current_entries() if e.data.get(CONF_DEVICE_ID) == user_input[CONF_DEVICE_ID]
            ]
            if existing:
                return self.async_abort(reason="already_configured")
            return self.async_create_entry(
                title=f"WARP Charger ({user_input[CONF_DEVICE_ID]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )
