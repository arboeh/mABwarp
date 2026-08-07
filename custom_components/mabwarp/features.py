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


def has_feature_or_default(features: list[str], feature: Feature) -> bool:
    """Return True if feature is present or features list is empty (default enabled)."""
    return feature.value in features or not features


def has_meters(features: list[str]) -> bool:
    """Return True if modern meter API is available, False if deprecated single-meter API."""
    if not features:
        return True
    if Feature.METERS.value in features:
        return True
    if Feature.METER.value in features and Feature.METERS.value not in features:
        _LOGGER.warning("Charger uses deprecated meter API, modern meters sensors skipped")
        return False
    return False
