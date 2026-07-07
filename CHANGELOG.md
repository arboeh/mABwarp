# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-06

### Added
- Initial HACS-compliant Release 1.0 structure
- Brand assets shipped locally in `brand/` directory (mABwarp integration)

### Fixed
- Fixed: `MabwarpFeaturesSensor._attr_name` was missing, now set to "Supported Features"
- Fixed: `NameError` for `_LOGGER` in `__init__.py` (corrected to use `LOGGER` from `const.py`)
- Fixed (critical): `METER_VALUE_ID_*` constants for Shelly 3EM Pro corrected:
  - Voltage: 1/2/3
  - Current: 13/17/21
  - Power: 39/48/57
  - Power total: 74
  - Energy total: 213

### Security
- Minimum Home Assistant version is 2026.3.0: the integration ships local
  brand assets in `brand/`, which require HA 2026.3+. All Python APIs used
  (`async_subscribe`, `async_publish`, entity base classes, `DeviceInfo`,
  `ConfigEntry`) are available in 2026.3.0 and do not require a newer release.
