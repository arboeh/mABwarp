# custom_components/mabwarp/sensor_day_ahead_prices.py

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_DEVICE_ID,
    CONF_WARP_VERSION,
    DAY_AHEAD_PRICE_SCALE_FACTOR,
    DOMAIN,
    TOPIC_DAY_AHEAD_PRICES_CONFIG,
    TOPIC_DAY_AHEAD_PRICES_PRICES,
    TOPIC_DAY_AHEAD_PRICES_STATE,
)
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpDayAheadPriceSensor(MabwarpMqttSensor):
    """Sensor for the current day ahead price."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_DAY_AHEAD_PRICES_STATE.format(prefix=topic_prefix),
            "Day Ahead Price",
            "current_price",
            "ct/kWh",
            None,
            SensorStateClass.MEASUREMENT,
            coordinator=None,
            conversion_factor=DAY_AHEAD_PRICE_SCALE_FACTOR,
            translation_key="day_ahead_price",
        )


class MabwarpDayAheadPricesForecastSensor(SensorEntity):
    """Sensor for the day ahead prices forecast array."""

    _attr_icon = "mdi:chart-line"
    _attr_native_value = None
    _attr_has_entity_name = True
    _attr_translation_key = "day_ahead_prices_forecast"

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the forecast sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_DAY_AHEAD_PRICES_PRICES.format(prefix=topic_prefix)
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
                prices = data.get("prices")
                if isinstance(prices, list) and len(prices) > 0:
                    first_price = prices[0]
                    if isinstance(first_price, int | float):
                        self._attr_native_value = first_price * DAY_AHEAD_PRICE_SCALE_FACTOR
                    else:
                        self._attr_native_value = None
                else:
                    self._attr_native_value = None
                self._attr_extra_state_attributes = {
                    "first_date": data.get("first_date"),
                    "resolution": data.get("resolution"),
                    "prices": prices if isinstance(prices, list) else [],
                }
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this sensor."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_{self._topic.replace('/', '_')}_forecast"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        warp_version = self._config_entry.data[CONF_WARP_VERSION]
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"WARP Charger {device_id}",
            manufacturer="Tinkerforge GmbH",
            model=warp_version,
        )


def build_day_ahead_prices_entities(entry, topic_prefix: str, features: list) -> list:
    """Build day ahead prices sensor entities."""
    has_day_ahead_prices = "day_ahead_prices" in features
    if not has_day_ahead_prices:
        return []

    entities = [
        MabwarpDayAheadPriceSensor(entry, topic_prefix),
        MabwarpDayAheadPricesForecastSensor(entry, topic_prefix),
    ]
    return entities
