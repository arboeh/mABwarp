# custom_components/mabwarp/sensor_solar_forecast.py

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_WARP_VERSION,
    DOMAIN,
    TOPIC_SOLAR_FORECAST_PLANES_CONFIG,
    TOPIC_SOLAR_FORECAST_PLANES_LIST,
    TOPIC_SOLAR_FORECAST_PLANES_STATE,
    TOPIC_SOLAR_FORECAST_STATE,
)
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpSolarForecastValueSensor(MabwarpMqttSensor):
    """Sensor for solar forecast values with -1 => None mapping."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, field_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_SOLAR_FORECAST_STATE.format(prefix=topic_prefix),
            f"Solar Forecast {field_name.replace('_', ' ').title()}",
            field_name,
            "Wh",
            SensorDeviceClass.ENERGY,
            None,
            coordinator=None,
        )

    def extract_field(self, data: dict) -> Any:
        value = super().extract_field(data)
        return None if value == -1 else value


class MabwarpSolarPlaneStateSensor(MabwarpMqttSensor):
    """Sensor for a single solar plane's state (place)."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, plane_idx: int) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_SOLAR_FORECAST_PLANES_STATE.format(prefix=topic_prefix, idx=plane_idx),
            f"Solar Plane {plane_idx} Place",
            "place",
            None,
            None,
            None,
            coordinator=None,
        )


class MabwarpSolarPlaneConfigSensor(SensorEntity):
    """Sensor for a single solar plane's config (name, wp)."""

    _attr_native_value = None
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str, plane_idx: int) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._topic = TOPIC_SOLAR_FORECAST_PLANES_CONFIG.format(prefix=topic_prefix, idx=plane_idx)
        self._unsubscribe = None
        self._plane_idx = plane_idx

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                self._attr_native_value = data.get("wp")
                self._attr_extra_state_attributes = {
                    "name": data.get("name"),
                    "place": data.get("place"),
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
        return f"{DOMAIN}_{device_id}_solar_plane_{self._plane_idx}_config"

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


def _discover_solar_planes(
    hass: HomeAssistant,
    entry,
    topic_prefix: str,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Discover solar plane entities dynamically."""
    future = asyncio.get_event_loop().create_future()

    def _planes_list_received(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, list):
                future.set_result([int(x) for x in data])
            else:
                future.set_result([])
        except (json.JSONDecodeError, TypeError, ValueError):
            future.set_result([])

    async def _discover_solar_planes():
        unsub = await async_subscribe(
            hass,
            TOPIC_SOLAR_FORECAST_PLANES_LIST.format(prefix=topic_prefix),
            _planes_list_received,
            0,
        )
        try:
            plane_indices = await asyncio.wait_for(future, timeout=3)
        except TimeoutError:
            plane_indices = []
        finally:
            unsub()

        if not plane_indices:
            for idx in range(10):
                fut = asyncio.get_event_loop().create_future()

                def _make_callback(f, i):
                    def _plane_received(msg) -> None:
                        try:
                            payload = msg.payload
                            if isinstance(payload, bytes):
                                payload = payload.decode("utf-8")
                            data = json.loads(payload)
                            if isinstance(data, dict) and "place" in data:
                                f.set_result(i)
                            else:
                                f.set_result(None)
                        except (json.JSONDecodeError, TypeError, ValueError):
                            f.set_result(None)

                    return _plane_received

                unsub2 = await async_subscribe(
                    hass,
                    TOPIC_SOLAR_FORECAST_PLANES_STATE.format(prefix=topic_prefix, idx=idx),
                    _make_callback(fut, idx),
                    0,
                )
                try:
                    result = await asyncio.wait_for(fut, timeout=0.5)
                    if result is not None:
                        plane_indices.append(result)
                except TimeoutError:
                    pass
                finally:
                    unsub2()

        plane_entities = []
        for idx in plane_indices:
            plane_entities.extend(
                [
                    MabwarpSolarPlaneStateSensor(entry, topic_prefix, idx),
                    MabwarpSolarPlaneConfigSensor(entry, topic_prefix, idx),
                ]
            )

        if plane_entities:
            async_add_entities(plane_entities)

    hass.async_create_task(_discover_solar_planes())


def build_solar_forecast_entities(
    hass: HomeAssistant,
    entry,
    topic_prefix: str,
    features: list,
    async_add_entities: AddEntitiesCallback,
) -> list:
    """Build solar forecast sensor entities."""
    has_solar_forecast = "solar_forecast" in features
    if not has_solar_forecast:
        return []

    entities = [
        MabwarpSolarForecastValueSensor(entry, topic_prefix, "wh_today"),
        MabwarpSolarForecastValueSensor(entry, topic_prefix, "wh_today_remaining"),
        MabwarpSolarForecastValueSensor(entry, topic_prefix, "wh_tomorrow"),
    ]

    _discover_solar_planes(hass, entry, topic_prefix, async_add_entities)

    return entities
