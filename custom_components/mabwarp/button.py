# custom_components/mabwarp/button.py

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.components.mqtt.client import async_publish
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
    TOPIC_CHARGE_LIMITS_RESTART,
    TOPIC_EVSE_START,
    TOPIC_EVSE_STOP,
)
from .entity_base import MabwarpEntityBase
from .features import Feature, has_feature

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp buttons."""
    topic_prefix = entry.data[CONF_TOPIC_PREFIX]
    features = entry.data.get("features", [])

    entities = [
        MabwarpButtonBase(
            entry,
            "start_charging",
            TOPIC_EVSE_START.format(prefix=topic_prefix),
            "mdi:play-circle",
        ),
        MabwarpButtonBase(
            entry,
            "stop_charging",
            TOPIC_EVSE_STOP.format(prefix=topic_prefix),
            "mdi:stop-circle",
        ),
    ]

    if has_feature(features, Feature.CHARGE_LIMITS):
        entities.append(
            MabwarpButtonBase(
                entry,
                "restart_charge_limits",
                TOPIC_CHARGE_LIMITS_RESTART.format(prefix=topic_prefix),
                "mdi:restart",
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )

    async_add_entities(entities)


class MabwarpButtonBase(MabwarpEntityBase, ButtonEntity):
    """Base class for mABwarp MQTT buttons."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        translation_key: str,
        topic: str,
        icon: str,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the button."""
        super().__init__(entity_category=entity_category)
        self._config_entry = config_entry
        self._topic = topic
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_icon = icon

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.info("Button pressed: %s", self._topic)
        await async_publish(
            self.hass,
            self._topic,
            "null",
            qos=0,
            retain=False,
            encoding="utf-8",
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this button."""
        return self._build_unique_id(self._topic.replace("/", "_"))
