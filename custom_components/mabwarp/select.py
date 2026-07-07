# custom_components/mabwarp/select.py

from __future__ import annotations

import json
import logging

from homeassistant.components.mqtt.client import async_publish, async_subscribe
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# ASSUMPTION: CHARGE_MODE_MAP values are assumed based on typical WARP web UI
# mappings (0=Standby, 1=Min, 2=PV, 3=Min+PV). Not yet verified against real
# hardware or official documentation. See const.py for the definition.
from .const import (
    CHARGE_MODE_MAP,
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    CONF_WARP_VERSION,
    DOMAIN,
    TOPIC_POWER_MANAGER_CHARGE_MODE,
    TOPIC_POWER_MANAGER_CHARGE_MODE_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp selects."""
    features = entry.data.get("features", [])
    if "power_manager" in features:
        async_add_entities([MabwarpChargeModeSelect(entry)])


class MabwarpChargeModeSelect(SelectEntity):
    """Select entity for WARP Power Manager charge mode.

    WARNING: The option labels are based on an unverified assumption about
    the WARP web UI and may not exactly match the charger firmware or
    official documentation. See const.py CHARGE_MODE_MAP for details.
    """

    _attr_icon = "mdi:ev-station"
    _attr_has_entity_name = True
    _attr_translation_key = "power_manager_charge_mode"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        self._config_entry = config_entry
        self._unsubscribe = None
        self._attr_options = list(CHARGE_MODE_MAP.values())
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic when added to Home Assistant."""

        def message_received(msg: ReceiveMessage) -> None:
            try:
                payload = msg.payload
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                mode = data.get("mode")
                if mode is not None:
                    self._attr_current_option = CHARGE_MODE_MAP.get(int(mode), f"Unknown ({mode})")
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as err:
                _LOGGER.warning("Failed to parse MQTT message on %s: %s", self._topic, err)

        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        self._topic = TOPIC_POWER_MANAGER_CHARGE_MODE.format(prefix=topic_prefix)
        self._unsubscribe = await async_subscribe(self.hass, self._topic, message_received, 0)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    async def async_select_option(self, option: str) -> None:
        """Select a new option."""
        mode = next((k for k, v in CHARGE_MODE_MAP.items() if v == option), None)
        if mode is None:
            return
        topic_prefix = self._config_entry.data[CONF_TOPIC_PREFIX]
        topic = TOPIC_POWER_MANAGER_CHARGE_MODE_UPDATE.format(prefix=topic_prefix)
        payload = json.dumps({"mode": mode})
        await async_publish(
            self.hass,
            topic,
            payload,
            qos=0,
            retain=False,
            encoding="utf-8",
        )
        self._attr_current_option = option
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        """Return unique ID for this select entity."""
        device_id = self._config_entry.data[CONF_DEVICE_ID]
        return f"{DOMAIN}_{device_id}_charge_mode"

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
