# custom_components/mabwarp/const.py

DOMAIN = "mabwarp"
CONF_TOPIC_PREFIX = "topic_prefix"
CONF_DEVICE_ID = "device_id"
CONF_WARP_VERSION = "warp_version"

DEFAULT_TOPIC_PREFIX = "warp"

WARP_VERSIONS = ["WARP2", "WARP3", "WARP4"]

# Topic templates – format with prefix
TOPIC_EVSE_STATE = "{prefix}/evse/state"
TOPIC_EVSE_LOW_LEVEL = "{prefix}/evse/low_level_state"
TOPIC_METER_VALUES = "{prefix}/meters/1/values"
TOPIC_EVSE_EXT_CURRENT = "{prefix}/evse/external_current"
TOPIC_CHARGE_MANAGER = "{prefix}/charge_manager/state"
TOPIC_NFC_LAST_TAG = "{prefix}/nfc/last_seen"
TOPIC_EVSE_SET_EXT_CURRENT = "{prefix}/evse/set_external_current"
TOPIC_EVSE_START = "{prefix}/evse/start_charging"
TOPIC_EVSE_STOP = "{prefix}/evse/stop_charging"
TOPIC_EVSE_USER_ENABLED = "{prefix}/evse/user_enabled"
TOPIC_EVSE_SET_USER_ENABLED = "{prefix}/evse/set_user_enabled"
