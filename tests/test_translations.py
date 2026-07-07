"""Tests that translation keys in code match the translation JSON files."""

from custom_components.mabwarp.const import (
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
)


def _load_entity_sensor(lang: str) -> dict:
    import json
    import pathlib

    path = pathlib.Path(__file__).parent.parent / "custom_components" / "mabwarp" / "translations" / f"{lang}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)["entity"]["sensor"]


METER_TRANSLATION_KEYS = (
    "voltage_l1",
    "voltage_l2",
    "voltage_l3",
    "current_l1",
    "current_l2",
    "current_l3",
    "power_l1",
    "power_l2",
    "power_l3",
    "power_total",
    "energy_total",
)


def test_meter_translation_keys_match_meter_value_ids():
    """Meter entities use descriptive string translation_keys; JSON must match."""
    for lang in ("en", "de"):
        sensor_keys = _load_entity_sensor(lang)
        for key in METER_TRANSLATION_KEYS:
            assert key in sensor_keys, f"{lang}.json is missing meter translation key '{key}'"
