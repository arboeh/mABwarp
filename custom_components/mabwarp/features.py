# custom_components/mabwarp/features.py

from __future__ import annotations

import logging
from enum import StrEnum

_LOGGER = logging.getLogger(__name__)


class Feature(StrEnum):
    METERS = "meters"
    METER = "meter"
    NFC = "nfc"
    CHARGE_TRACKER = "charge_tracker"
    DAY_AHEAD_PRICES = "day_ahead_prices"
    POWER_MANAGER = "power_manager"
    CHARGE_LIMITS = "charge_limits"
    SOLAR_FORECAST = "solar_forecast"
    TEMPERATURES = "temperatures"
    P14A_ENWG = "p14a_enwg"
    ETHERNET = "ethernet"


def has_feature(features: list[str], feature: Feature) -> bool:
    return feature.value in features


def has_meters(features: list[str]) -> bool:
    has_meters = "meters" in features or not features
    if "meter" in features and "meters" not in features:
        has_meters = False
        _LOGGER.warning("Charger uses deprecated meter API, modern meters sensors skipped")
    return has_meters
