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
TOPIC_EVSE_SET_USER_ENABLED = "{prefix}/evse/set_user_enabled"
