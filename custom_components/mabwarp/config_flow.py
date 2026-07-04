# custom_components/mabwarp/config_flow.py

from __future__ import annotations

import asyncio
import json
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.mqtt.client import async_subscribe

from .const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    TOPIC_INFO_FEATURES,
    WARP_VERSIONS,
)

_LOGGER = logging.getLogger(__name__)

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

            features: list[str] = []
            topic = TOPIC_INFO_FEATURES.format(prefix=user_input[CONF_TOPIC_PREFIX])
            future: asyncio.Future[list[str]] = asyncio.get_event_loop().create_future()

            def _features_message_received(msg) -> None:
                try:
                    payload = msg.payload
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")
                    data = json.loads(payload)
                    if isinstance(data, list):
                        future.set_result([str(item) for item in data])
                    else:
                        future.set_result([])
                except (json.JSONDecodeError, TypeError, ValueError) as err:
                    _LOGGER.warning("Failed to parse features message: %s", err)
                    future.set_result([])

            unsubscribe = await async_subscribe(self.hass, topic, _features_message_received, 0)
            try:
                features = await asyncio.wait_for(future, timeout=5)
            except TimeoutError:
                _LOGGER.warning("Feature detection timed out for %s", user_input[CONF_TOPIC_PREFIX])
                features = []
            finally:
                unsubscribe()

            user_input[CONF_FEATURES] = features
            return self.async_create_entry(
                title=f"WARP Charger ({user_input[CONF_DEVICE_ID]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )
