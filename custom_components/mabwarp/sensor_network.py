# custom_components/mabwarp/sensor_network.py

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_DEVICE_ID,
    CONF_WARP_VERSION,
    DOMAIN,
    TOPIC_ETHERNET_STATE,
    TOPIC_WIFI_STATE,
)
from .sensor_base import MabwarpMqttSensor, async_subscribe

_LOGGER = logging.getLogger(__name__)


class MabwarpWifiSignalStrengthSensor(MabwarpMqttSensor):
    """Sensor for WiFi signal strength (RSSI)."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_WIFI_STATE.format(prefix=topic_prefix),
            "WiFi Signal Strength",
            "sta_rssi",
            "dBm",
            SensorDeviceClass.SIGNAL_STRENGTH,
            SensorStateClass.MEASUREMENT,
            coordinator=None,
            translation_key="wifi_signal_strength",
        )


class MabwarpWifiIpAddressSensor(MabwarpMqttSensor):
    """Sensor for WiFi IP address."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_WIFI_STATE.format(prefix=topic_prefix),
            "WiFi IP Address",
            "sta_ip",
            None,
            None,
            None,
            coordinator=None,
            translation_key="wifi_ip_address",
        )


class MabwarpWifiConnectionStateSensor(MabwarpMqttSensor):
    """Sensor for WiFi connection state (enum int)."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_WIFI_STATE.format(prefix=topic_prefix),
            "WiFi Connection State",
            "connection_state",
            None,
            None,
            None,
            coordinator=None,
            translation_key="wifi_connection_state",
        )


class MabwarpEthernetLinkSpeedSensor(MabwarpMqttSensor):
    """Sensor for Ethernet link speed."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_ETHERNET_STATE.format(prefix=topic_prefix),
            "Ethernet Link Speed",
            "link_speed",
            "Mbit/s",
            SensorDeviceClass.DATA_RATE,
            SensorStateClass.MEASUREMENT,
            coordinator=None,
            translation_key="ethernet_link_speed",
        )


class MabwarpEthernetIpAddressSensor(MabwarpMqttSensor):
    """Sensor for Ethernet IP address."""

    def __init__(self, config_entry: ConfigEntry, topic_prefix: str) -> None:
        """Initialize the sensor."""
        super().__init__(
            config_entry,
            TOPIC_ETHERNET_STATE.format(prefix=topic_prefix),
            "Ethernet IP Address",
            "ip",
            None,
            None,
            None,
            coordinator=None,
            translation_key="ethernet_ip_address",
        )


def build_network_entities(entry, topic_prefix: str, features: list) -> list:
    """Build network sensor entities."""
    entities = [
        MabwarpWifiSignalStrengthSensor(entry, topic_prefix),
        MabwarpWifiIpAddressSensor(entry, topic_prefix),
        MabwarpWifiConnectionStateSensor(entry, topic_prefix),
    ]

    has_ethernet = "ethernet" in features or not features
    if has_ethernet:
        entities.extend(
            [
                MabwarpEthernetLinkSpeedSensor(entry, topic_prefix),
                MabwarpEthernetIpAddressSensor(entry, topic_prefix),
            ]
        )

    return entities
