# custom_components/mabwarp/const.py

import logging

DOMAIN = "mabwarp"
CONF_FEATURES = "features"

CONF_TOPIC_PREFIX = "topic_prefix"
CONF_DEVICE_ID = "device_id"
CONF_WARP_VERSION = "warp_version"

DEFAULT_TOPIC_PREFIX = "warp"

WARP_VERSIONS = ["WARP2", "WARP3", "WARP4"]

# Topic templates - format with prefix
TOPIC_EVSE_STATE = "{prefix}/evse/state"
TOPIC_EVSE_LOW_LEVEL = "{prefix}/evse/low_level_state"
TOPIC_METER_VALUES = "{prefix}/meters/1/values"
TOPIC_METER_VALUE_IDS = "{prefix}/meters/1/value_ids"
TOPIC_EVSE_EXT_CURRENT = "{prefix}/evse/external_current"
TOPIC_EVSE_SET_EXT_CURRENT = "{prefix}/evse/set_external_current"
TOPIC_EVSE_START = "{prefix}/evse/start_charging"
TOPIC_EVSE_STOP = "{prefix}/evse/stop_charging"
TOPIC_CHARGE_MANAGER = "{prefix}/charge_manager/state"
TOPIC_NFC_LAST_TAG = "{prefix}/nfc/last_seen"
TOPIC_EVSE_SET_USER_ENABLED = "{prefix}/evse/set_user_enabled"
TOPIC_EVSE_USER_ENABLED = "{prefix}/evse/user_enabled"
TOPIC_INFO_FEATURES = "{prefix}/info/features"
TOPIC_INFO_VERSION = "{prefix}/info/version"
TOPIC_INFO_NAME = "{prefix}/info/name"
TOPIC_INFO_DISPLAY_NAME = "{prefix}/info/display_name"
TOPIC_CHARGE_TRACKER_STATE = "{prefix}/charge_tracker/state"
TOPIC_CHARGE_TRACKER_CURRENT = "{prefix}/charge_tracker/current_charge"
TOPIC_CHARGE_TRACKER_LAST = "{prefix}/charge_tracker/last_charges"

# Power Manager
TOPIC_POWER_MANAGER_CHARGE_MODE = "{prefix}/power_manager/charge_mode"
TOPIC_POWER_MANAGER_CHARGE_MODE_UPDATE = "{prefix}/power_manager/charge_mode_update"
TOPIC_POWER_MANAGER_STATE = "{prefix}/power_manager/state"
TOPIC_POWER_MANAGER_LOW_LEVEL_STATE = "{prefix}/power_manager/low_level_state"

# Solar Forecast
TOPIC_SOLAR_FORECAST_STATE = "{prefix}/solar_forecast/state"
TOPIC_SOLAR_FORECAST_PLANES_LIST = "{prefix}/solar_forecast/planes"
TOPIC_SOLAR_FORECAST_PLANES_STATE = "{prefix}/solar_forecast/planes/{idx}/state"
TOPIC_SOLAR_FORECAST_PLANES_CONFIG = "{prefix}/solar_forecast/planes/{idx}/config"

# Charge Limits
TOPIC_CHARGE_LIMITS_STATE = "{prefix}/charge_limits/state"
TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS = "{prefix}/charge_limits/default_limits"
TOPIC_CHARGE_LIMITS_DEFAULT_LIMITS_UPDATE = "{prefix}/charge_limits/default_limits_update"
TOPIC_CHARGE_LIMITS_RESTART = "{prefix}/charge_limits/restart"

# Temperatures
TOPIC_TEMPERATURES_STATE = "{prefix}/temperatures/state"

# P14A ENWG
TOPIC_P14A_ENWG_STATE = "{prefix}/p14a_enwg/state"

# Network Diagnostics
TOPIC_WIFI_STATE = "{prefix}/wifi/state"
TOPIC_ETHERNET_STATE = "{prefix}/ethernet/state"

# Day Ahead Prices
TOPIC_DAY_AHEAD_PRICES_STATE = "{prefix}/day_ahead_prices/state"
TOPIC_DAY_AHEAD_PRICES_PRICES = "{prefix}/day_ahead_prices/prices"
TOPIC_DAY_AHEAD_PRICES_CONFIG = "{prefix}/day_ahead_prices/config"
DAY_AHEAD_PRICE_SCALE_FACTOR = 0.0001

# Meter Value IDs from official WARP API
# https://docs.warp-charger.com/de/docs/interfaces/mqtt_http/api_reference/meters/
METER_VALUE_ID_VOLTAGE_L1 = 1
METER_VALUE_ID_VOLTAGE_L2 = 2
METER_VALUE_ID_VOLTAGE_L3 = 3
METER_VALUE_ID_CURRENT_L1 = 13
METER_VALUE_ID_CURRENT_L2 = 17
METER_VALUE_ID_CURRENT_L3 = 21
METER_VALUE_ID_POWER_L1 = 39
METER_VALUE_ID_POWER_L2 = 48
METER_VALUE_ID_POWER_L3 = 57
METER_VALUE_ID_POWER_TOTAL = 74
METER_VALUE_ID_ENERGY_TOTAL = 213

# Optional future extensions (Shelly 3EM Pro / additional WARP meter values):
# 33 - Summe Strom, 154 - Summe Scheinleistung,
# 209 - Wirkenergie Bezug, 211 - Wirkenergie Einspeisung,
# 357-359 - Leistungsfaktor je Phase

# ASSUMPTION: Charge Mode mapping is not yet verified against official
# WARP documentation or real hardware.
# Documentation sources:
#   - Documented modes (0-3): community-verified from Tinkerforge docs and web UI.
#   - Undocumented modes (5-9): community-sourced, not verified by Tinkerforge.
# TODO: verify against real hardware before production release.
# Verification methods:
#   1. Browser DevTools at real WARP web interface: observe HTTP PUT
#      payloads to /power_manager/charge_mode when changing modes.
#   2. mosquitto_sub on $PREFIX/power_manager/charge_mode while setting
#      each mode in the web interface and log resulting mode values.
CHARGE_MODE_MAP = {
    0: "Schnell",
    1: "Aus",
    2: "PV",
    3: "Min+PV",
    # Undocumented modes - community-sourced, not verified by Tinkerforge
    5: "Min",
    6: "Eco",
    7: "Eco+PV",
    8: "Eco+Min",
    9: "Eco+Min+PV",
}

# Config Error Flag bit definitions (ASSUMPTION - verify against real payload)
# Decoded as extra_state_attributes on the config_error_flags sensor
CONFIG_ERROR_FLAG_BITS = [
    "config_error_0",
    "config_error_1",
    "config_error_2",
    "config_error_3",
    "config_error_4",
    "config_error_5",
    "config_error_6",
    "config_error_7",
]

LOGGER = logging.getLogger(__name__)
