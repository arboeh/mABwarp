# custom_components/mabwarp/const.py

DOMAIN = "mabwarp"
CONF_FEATURES = "features"

CONF_TOPIC_PREFIX = "topic_prefix"
CONF_DEVICE_ID = "device_id"
CONF_WARP_VERSION = "warp_version"

DEFAULT_TOPIC_PREFIX = "warp"

WARP_VERSIONS = ["WARP2", "WARP3", "WARP4"]

# Topic templates – format with prefix
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

# Meter Value IDs from WARP3 value_ids list
METER_VALUE_ID_VOLTAGE_L1 = "13"
METER_VALUE_ID_VOLTAGE_L2 = "14"
METER_VALUE_ID_VOLTAGE_L3 = "15"
METER_VALUE_ID_CURRENT_L1 = "16"
METER_VALUE_ID_CURRENT_L2 = "17"
METER_VALUE_ID_CURRENT_L3 = "18"
METER_VALUE_ID_POWER_L1 = "19"
METER_VALUE_ID_POWER_L2 = "20"
METER_VALUE_ID_POWER_L3 = "21"
METER_VALUE_ID_POWER_TOTAL = "30"
METER_VALUE_ID_ENERGY_TOTAL = "40"

# ASSUMPTION: Charge Mode mapping is not yet verified against official
# WARP documentation or real hardware. 0=Standby, 1=Min, 2=PV, 3=Min+PV
# is assumed analog to the WARP web interface. TODO: verify before release.
CHARGE_MODE_MAP = {
    0: "Standby",
    1: "Min",
    2: "PV",
    3: "Min+PV",
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
