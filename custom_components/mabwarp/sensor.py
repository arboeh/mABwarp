# custom_components/mabwarp/sensor.py

from __future__ import annotations

import json
import logging

from homeassistant.components.mqtt.client import async_subscribe
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_FEATURES,
    CONF_TOPIC_PREFIX,
    METER_VALUE_ID_CURRENT_L1,
    METER_VALUE_ID_CURRENT_L2,
    METER_VALUE_ID_CURRENT_L3,
    METER_VALUE_ID_ENERGY_TOTAL,
    METER_VALUE_ID_POWER_L1,
    METER_VALUE_ID_POWER_L2,
    METER_VALUE_ID_POWER_L3,
    METER_VALUE_ID_POWER_TOTAL,
    METER_VALUE_ID_VOLTAGE_L1,
    METER_VALUE_ID_VOLTAGE_L2,
    METER_VALUE_ID_VOLTAGE_L3,
    TOPIC_CHARGE_TRACKER_CURRENT,
    TOPIC_CHARGE_TRACKER_LAST,
    TOPIC_CHARGE_TRACKER_STATE,
    TOPIC_METER_VALUE_IDS,
    TOPIC_METER_VALUES,
)
from .features import Feature, has_feature, has_feature_or_default, has_meters
from .sensor_base import MeterValueCoordinator, check_plausibility
from .sensor_charge_limits import build_charge_limits_entities
from .sensor_charge_tracker import build_charge_tracker_entities
from .sensor_day_ahead_prices import build_day_ahead_prices_entities
from .sensor_evse import build_evse_entities
from .sensor_misc import build_misc_entities
from .sensor_network import build_network_entities
from .sensor_power_manager import build_power_manager_entities
from .sensor_solar_forecast import build_solar_forecast_entities

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mABwarp sensors."""
    topic_prefix = entry.data[CONF_TOPIC_PREFIX]

    features = entry.data.get(CONF_FEATURES, [])
    has_meters_value = has_meters(features)
    has_nfc = has_feature_or_default(features, Feature.NFC)
    has_charge_tracker = has_feature_or_default(features, Feature.CHARGE_TRACKER)

    coordinator = MeterValueCoordinator(hass)

    async def value_ids_message_received(msg: ReceiveMessage) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, list):
                coordinator.update_value_ids_mapping(data)
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            _LOGGER.warning("Failed to parse value_ids message: %s", err)

    async def values_message_received(msg: ReceiveMessage) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, list):
                coordinator.store_values(data)
                check_plausibility(coordinator)
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            _LOGGER.warning("Failed to parse values message: %s", err)

    unsubscribe_value_ids = await async_subscribe(
        hass,
        TOPIC_METER_VALUE_IDS.format(prefix=topic_prefix),
        value_ids_message_received,
        0,
    )
    unsubscribe_values = await async_subscribe(
        hass,
        TOPIC_METER_VALUES.format(prefix=topic_prefix),
        values_message_received,
        0,
    )
    coordinator.set_unsubscribe_callbacks(unsubscribe_value_ids, unsubscribe_values)

    entities = []

    entities.extend(build_evse_entities(entry, topic_prefix, coordinator, features))
    entities.extend(build_charge_tracker_entities(entry, topic_prefix, features))
    entities.extend(build_power_manager_entities(entry, topic_prefix, features))
    entities.extend(build_solar_forecast_entities(hass, entry, topic_prefix, features, async_add_entities))
    entities.extend(build_charge_limits_entities(entry, topic_prefix, features))
    entities.extend(build_misc_entities(hass, entry, topic_prefix, features, async_add_entities))
    entities.extend(build_day_ahead_prices_entities(entry, topic_prefix, features))
    entities.extend(build_network_entities(entry, topic_prefix, features))

    unique_ids = [entity.unique_id for entity in entities]
    duplicate_ids = [uid for uid in unique_ids if unique_ids.count(uid) > 1]
    if duplicate_ids:
        raise ValueError(f"Duplicate unique_ids found: {duplicate_ids}")

    async_add_entities(entities)
