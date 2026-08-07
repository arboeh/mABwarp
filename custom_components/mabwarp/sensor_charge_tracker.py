# custom_components/mabwarp/sensor_charge_tracker.py

from __future__ import annotations

import datetime
import json
import logging
from typing import Any

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_TOPIC_PREFIX,
    TOPIC_CHARGE_TRACKER_CURRENT,
    TOPIC_CHARGE_TRACKER_LAST,
    TOPIC_CHARGE_TRACKER_STATE,
)
from .entity_base import MabwarpEntityBase
from .features import Feature, has_feature_or_default
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpCurrentChargeUserIDSensor(MabwarpMqttSensor):
    """Sensor for current charge user ID with idle-state handling."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=topic_prefix),
            "Current Charge User ID",
            "user_id",
            None,
            None,
            None,
            coordinator=None,
            translation_key="current_charge_user_id",
        )

    def extract_field(self, data: dict) -> Any:
        value = super().extract_field(data)
        return None if value == -1 else value


class MabwarpLastChargeSensor(MabwarpEntityBase, SensorEntity):
    """Sensor for the most recent entry in charge_tracker/last_charges."""

    _attr_icon = "mdi:ev-station"
    _attr_native_value = None
    _attr_has_entity_name = True
    _attr_translation_key = "last_charge_energy"

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the last charge sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_CHARGE_TRACKER_LAST.format(prefix=topic_prefix)
        self._unsubscribe = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                if not isinstance(data, list) or len(data) == 0:
                    self._attr_native_value = None
                    self._attr_extra_state_attributes = {}
                    _LOGGER.warning("Received empty last_charges array")
                    self._schedule_state_update()
                    return
                last = data[-1]
                energy = last.get("energy_charged")
                self._attr_native_value = energy
                self._attr_extra_state_attributes = {
                    "charge_duration": last.get("charge_duration"),
                    "user_id": last.get("user_id"),
                    "timestamp": datetime.datetime.fromtimestamp(
                        last.get("timestamp_minutes", 0) * 60,
                        tz=datetime.UTC,
                    ).isoformat(),
                }
                self._reset_parse_error_count()
                self._schedule_state_update()
            except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
                KeyError,
            ) as err:
                self._handle_parse_error(err, self._topic)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        return self._build_unique_id(f"{self._topic.replace('/', '_')}_last_charge")


def build_charge_tracker_entities(entry, topic_prefix: str, features: list) -> list:
    """Build charge tracker sensor entities."""
    has_charge_tracker = has_feature_or_default(features, Feature.CHARGE_TRACKER)
    if not has_charge_tracker:
        return []

    entities = [
        MabwarpMqttSensor(
            entry,
            TOPIC_CHARGE_TRACKER_STATE.format(prefix=topic_prefix),
            "Tracked Charges",
            "tracked_charges",
            None,
            None,
            None,
            coordinator=None,
            translation_key="tracked_charges",
        ),
        MabwarpMqttSensor(
            entry,
            TOPIC_CHARGE_TRACKER_CURRENT.format(prefix=topic_prefix),
            "Current Charge Meter Start",
            "meter_start",
            "kWh",
            SensorDeviceClass.ENERGY,
            None,
            coordinator=None,
            translation_key="current_charge_meter_start",
        ),
        MabwarpCurrentChargeUserIDSensor(entry, topic_prefix),
        MabwarpLastChargeSensor(entry, topic_prefix),
    ]
    return entities
