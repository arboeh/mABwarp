<!-- notes/README.md – Internal Developer Notes -->

# mABwarp – Developer Notes


## Project Structure
Brief explanation of each file and its role:


### Integration core
- `custom_components/mabwarp/const.py` – all constants, topic templates, config keys
- `custom_components/mabwarp/config_flow.py` – UI setup flow, validation, duplicate check
- `custom_components/mabwarp/__init__.py` – entry setup/unload, platform forwarding
- `custom_components/mabwarp/manifest.json` – integration metadata, HA dependencies
- `custom_components/mabwarp/strings.json` – source of truth for all translatable strings
- `custom_components/mabwarp/translations/en.json` – English translations
- `custom_components/mabwarp/translations/de.json` – German translations


### Entity platforms
- `custom_components/mabwarp/sensor.py` – sensor platform entry point, duplicate-ID check, coordinator setup
- `custom_components/mabwarp/sensor_base.py` – `MabwarpMqttSensor` base class, `MeterValueCoordinator`, `check_plausibility`
- `custom_components/mabwarp/sensor_evse.py` – EVSE state, low-level, meter-value, and NFC sensors
- `custom_components/mabwarp/sensor_charge_tracker.py` – charge tracker (current user, last charge, tracked charges)
- `custom_components/mabwarp/sensor_power_manager.py` – power manager (charge mode, config errors, low-level power)
- `custom_components/mabwarp/sensor_solar_forecast.py` – solar forecast values and dynamic plane discovery
- `custom_components/mabwarp/sensor_charge_limits.py` – charge limits timestamps and energy sensors
- `custom_components/mabwarp/sensor_misc.py` – features, info, charge manager, temperature, and P14A ENWG sensors
- `custom_components/mabwarp/number.py` – bidirectional charging current control
- `custom_components/mabwarp/button.py` – write-only start/stop buttons
- `custom_components/mabwarp/switch.py` – bidirectional user enable/disable


### Tests
- `tests/conftest.py` – shared fixtures (MockConfigEntry)
- `tests/test_config_flow.py` – config flow unit tests
- `tests/test_sensor.py` – sensor setup/integration tests (duplicate-ID check, discovery tasks)
- `tests/test_sensor_base.py` – base sensor class, coordinator, extract_field tests
- `tests/test_sensor_evse.py` – EVSE, meter, and NFC sensor tests
- `tests/test_sensor_charge_tracker.py` – charge tracker sensor tests
- `tests/test_sensor_power_manager.py` – power manager sensor tests
- `tests/test_sensor_solar_forecast.py` – solar forecast sensor tests
- `tests/test_sensor_charge_limits.py` – charge limits sensor tests
- `tests/test_sensor_misc.py` – misc sensor tests (features, temperature, P14A ENWG)
- `tests/test_number.py` – number entity unit tests
- `tests/test_button.py` – button entity unit tests
- `tests/test_switch.py` – switch entity unit tests


### Project config
- `pyproject.toml` – all project config: dependencies, pytest, ruff (single source of truth)
- `hacs.json` – HACS metadata
- `.gitignore` – standard Python + HA ignores


### CI/CD
- `.github/workflows/validate.yaml` – HACS validation + hassfest on push/PR
- `.github/workflows/lint.yaml` – ruff lint + format check on push/PR


---


## Adding a New Sensor
1. Add topic constant to `const.py` if needed
2. Add the sensor to the appropriate `sensor_*.py` module:
   - EVSE / meter / NFC → `sensor_evse.py`
   - Charge tracker → `sensor_charge_tracker.py`
   - Power manager → `sensor_power_manager.py`
   - Solar forecast → `sensor_solar_forecast.py`
   - Charge limits → `sensor_charge_limits.py`
   - Info / features / temperature / P14A ENWG / charge manager → `sensor_misc.py`
   - Generic MQTT sensor → extend `sensor_base.py` and add a `build_*` call in `sensor.py`
3. Add translation key to `translations/en.json`, `translations/de.json` and `strings.json`
4. Add test case to the corresponding `tests/test_sensor_*.py`


## Adding a New Entity Type (e.g. select, text)
1. Create new platform file (e.g. `select.py`) following pattern of `switch.py`
2. Add platform name to `PLATFORMS` list in `__init__.py`
3. Add entries to `translations/en.json`, `translations/de.json` and `strings.json`
4. Add test file `tests/test_select.py`
5. GitHub Actions lint will catch syntax errors automatically on next push


---


## WARP Charger MQTT Topic Reference
Full API: [https://docs.warp-charger.com/de/docs/interfaces/mqtt_http/api_reference/mqtt/](https://docs.warp-charger.com/de/docs/interfaces/mqtt_http/api_reference/mqtt/)


## Known Topic Differences by Version
| Topic                  | WARP2 | WARP3     | WARP4      |
|------------------------|-------|-----------|------------|
| evse/state             | ✅    | ✅        | ✅         |
| evse/low_level_state   | ✅    | ✅        | ✅         |
| evse/external_current  | ✅    | ✅        | ✅         |
| evse/user_enabled      | ✅    | ✅        | ✅         |
| evse/start_charging    | ✅    | ✅        | ✅         |
| evse/stop_charging     | ✅    | ✅        | ✅         |
| meter/values           | ✅    | ⚠️ legacy | ⚠️ legacy  |
| meters/{slot}/values   | ❌    | ✅        | 🔍 verify  |
| nfc/last_seen          | ✅    | ✅        | 🔍 verify  |
| charge_manager/state   | ✅    | ✅        | 🔍 verify  |

> ⚠️ `meter/values` is the legacy single-meter API (values are null if no direct meter attached).
> WARP3+ uses `meters/{slot}/values` where slot is typically `1` for the first external meter (e.g. Shelly Pro 3EM via Modbus TCP).
> The slot is currently hardcoded to `1` in `const.py`.


---


## Running Tests Locally
```powershell
.\test-local.ps1
```


Or manually:
```powershell
uv sync --dev
uv run pytest tests/ -v
```


## Running Linter Locally
```powershell
ruff check custom_components/mabwarp/
ruff format custom_components/mabwarp/
```


---


## Release Process
1. Update `version` in `custom_components/mabwarp/manifest.json` – this is the single source of truth
2. Create GitHub Release with tag `vX.Y.Z` matching the version
3. HACS picks up the new release automatically

> ℹ️ `pyproject.toml` reads the version dynamically from `manifest.json` via hatchling.
> Never edit the version in `pyproject.toml` directly.


---


## TODO / Open Items
- [ ] Verify WARP4 topic compatibility
- [ ] Make meter slot configurable (currently hardcoded to slot 1 in const.py)
- [ ] Verify correct array index mapping for meters/values per WARP version
- [ ] Add select entity for charge mode
- [ ] Add energy dashboard support (long-term statistics)
- [ ] Write integration tests with mocked MQTT broker
- [ ] Add pytest run to GitHub Actions (lint.yaml or separate test.yaml)
- [ ] Submit to HACS default repository once stable
