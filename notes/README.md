<!-- notes/README.md - Internal Developer Notes -->

# mABwarp - Developer Notes

Interne Anleitung zum Erstellen von **Public Releases** für mABwarp.


## Repository-Setup

### Single Repo mit `main` Branch

```
mABwarp/
├── main        # 🌟 Production Releases (git tag v1.0.0)
└── Remote: origin → https://github.com/arboeh/mABwarp
```

**Workflow:**

1. **Development** auf `main` Branch
2. **Production** → Commit auf `main` → `git tag v1.0.0`

---

## Voraussetzungen

- [ ] Virtual Environment: `uv sync --dev --extra dev`
- [ ] Tests: `uv run pytest tests/ -v --cov=custom_components.mabwarp --cov-report=term-missing`
- [ ] Lint: `ruff check custom_components/mabwarp/ tests/`
- [ ] Format: `ruff format --check custom_components/mabwarp/ tests/`
- [ ] Pre-commit: `pre-commit run --all-files` ✅ **passed**
- [ ] VS Code: `even-better-toml` + `ruff`
- [ ] `manifest.json` version = Production-Version (Single Source of Truth)
- [ ] Hassfest-Validierung lokal (muss vor jedem Push ausgeführt werden): `hassfest`

### Remote Setup (einmalig)

```powershell
git remote -v  # Sollte origin → GitHub zeigen
```

---

## Pre-commit Hooks

`.pre-commit-config.yaml` prüft automatisch:

- ✅ Ruff Linting & Formatting
- ✅ Trailing Whitespace
- ✅ End-of-File Fixer
- ✅ JSON/YAML Syntax
- ✅ Merge Conflicts
- ✅ Hassfest forbidden keys in `strings.json` (via `tests/test_translations.py`)


---

## Version Management

`manifest.json` ist die **Single Source of Truth** für die Version:

```json
// custom_components/mabwarp/manifest.json
{
  "version": "1.0.0"
}
```

> ℹ️ `pyproject.toml` liest die Version dynamisch aus `manifest.json` über `get_version.py` (hatchling `source = "code"`).
> **Nie** die Version in `pyproject.toml` direkt editieren.

### Version aktualisieren

```powershell
# 1. Version in manifest.json aktualisieren
# 2. get_version.py liest sie automatisch

# Alternative: Version synchronisieren (manifest.json -> pyproject.toml)
pwsh scripts/sync-manifest.ps1 -WhatIf
pwsh scripts/sync-manifest.ps1 -Version "1.0.1"
```

---

## Lint, Format und Tests ausführen

```powershell
ruff check custom_components/mabwarp/ tests/
ruff format --check custom_components/mabwarp/ tests/
pre-commit run --all-files
uv run pytest tests/ -v --cov=custom_components.mabwarp --cov-report=term-missing
```

**Erwartung:**
- Ruff Check --- ✅ no errors
- Ruff Format --- ✅ no changes needed
- Pre-commit --- ✅ all hooks passed
- Pytest --- ✅ alle Tests passed


---

## Hassfest lokal prüfen (**verpflichtend vor jedem Release**)

```powershell
hassfest
```

> Verhindert, dass verbotene Schlüssel in `strings.json` (z. B. `selector`, `required`, `example` in Service-Feldern) erst in der CI auffallen. Muss vor jedem Commit ausgeführt werden.


---

## CHANGELOG.md aktualisieren

```markdown
## [v1.0.1] - 2026-08-07

### Added

- ...

### Fixed

- ...
```


---

## Commit & Push (main Branch)

```powershell
git checkout main
git pull origin main
git add .
git commit -m "feat: v1.0.1 - < Kurzbeschreibung >"
git push origin main
```


---

## Production Release

### 1. Dev-Tag / Produktiv-Tag erstellen

```powershell
git checkout main
git tag v1.0.0
git push origin v1.0.0
```

### 2. GitHub Release (Public)

```
GitHub → Releases → Draft new release
├── Tag: v1.0.0
├── Branch: main
├── Title: mABwarp v1.0.0
└── Notes: Copy aus CHANGELOG.md
```

**Status:** **Published** (öffentlich für HACS)


---

## Update-Testing (optional)

```powershell
# Vor Release in HA testen:
# 1. HACS → Custom Repository → mABwarp (main Branch)
# 2. v1.0.0 installieren
# 3. Config Flow: Topic Prefix + Device ID eingeben
# 4. Alle Sensoren/Buttons/Switches/Number-Entities prüfen
# 5. MQTT-Topics abonnieren und Plausibilität prüfen
```


---

## Troubleshooting

### Tests schlagen fehl

```powershell
Remove-Item -Recurse -Force .venv
uv sync --dev --extra dev
uv run pytest tests/ -v --cov=custom_components.mabwarp --cov-report=term-missing
```

### Ruff meldet Fehler

```powershell
ruff check custom_components/mabwarp/ tests/ --fix
ruff format custom_components/mabwarp/ tests/
```

### Pre-commit Fehlermeldung

```powershell
pre-commit clean
pre-commit install
```

### Hassfest schlägt fehl

```powershell
hassfest
# Häufigste Ursache: verbotene Schlüssel (selector/required/example)
# in custom_components/mabwarp/strings.json unter "services"
```

### HACS zeigt alte Version

```
GitHub → Releases → Latest muss v1.0.0 sein
HACS → Reload → Update verfügbar
```


---

## Checkliste vor Release

**Kopiere in GitHub Issue:**

```markdown
## Release v1.0.0 Checklist

### Pre-commit / Lint / Tests

- [ ] `ruff check custom_components/mabwarp/ tests/` ✅ passed
- [ ] `ruff format --check custom_components/mabwarp/ tests/` ✅ passed
- [ ] `pre-commit run --all-files` ✅ passed
- [ ] `hassfest` ✅ passed
- [ ] `uv run pytest tests/ -v --cov=custom_components.mabwarp --cov-report=term-missing` ✅ passed
- [ ] `manifest.json` version = "1.0.0"

### Translation Consistency

- [ ] `strings.json` / `translations/de.json` / `translations/en.json` Keys identisch
- [ ] Keine hassfest-forbidden keys (`selector`, `required`, `example` in Service-Feldern)

### Release

- [ ] CHANGELOG.md aktualisiert
- [ ] `git push origin main`
- [ ] `git tag v1.0.0`
- [ ] `git push origin v1.0.0`
- [ ] GitHub Release (Published)

### HACS

- [ ] HACS zeigt Update (Restart erforderlich)
```


---

## Quick Reference

```powershell
# Development
git checkout main
# ... develop ...
pre-commit run --all-files
ruff check custom_components/mabwarp/ tests/
ruff format --check custom_components/mabwarp/ tests/
hassfest
uv run pytest tests/ -v --cov=custom_components.mabwarp --cov-report=term-missing
git commit -m "feat: XYZ"
git push origin main

# Production Release
git tag v1.0.0
git push origin v1.0.0
```

**Dauer:** Public Release **~5 Min** 🎉


---


## Project Structure

Brief explanation of each file and its role:


### Integration core
- `custom_components/mabwarp/const.py` - all constants, topic templates, config keys
- `custom_components/mabwarp/config_flow.py` - UI setup flow, validation, duplicate check
  - `custom_components/mabwarp/__init__.py` - entry setup/unload, platform forwarding, imports `__version__` from `get_version.py`
- `custom_components/mabwarp/manifest.json` - integration metadata, HA dependencies, **version (Single Source of Truth)**
- `custom_components/mabwarp/get_version.py` - reads `__version__` from `manifest.json` at build time (hatchling)
- `custom_components/mabwarp/strings.json` - source of truth for all translatable strings
- `custom_components/mabwarp/translations/en.json` - English translations
- `custom_components/mabwarp/translations/de.json` - German translations


### Entity platforms
- `custom_components/mabwarp/sensor.py` - sensor platform entry point, duplicate-ID check, coordinator setup
- `custom_components/mabwarp/sensor_base.py` - `MabwarpMqttSensor` base class, `MeterValueCoordinator`, `check_plausibility`
- `custom_components/mabwarp/sensor_evse.py` - EVSE state, low-level, meter-value, and NFC sensors
- `custom_components/mabwarp/sensor_charge_tracker.py` - charge tracker (current user, last charge, tracked charges)
- `custom_components/mabwarp/sensor_power_manager.py` - power manager (charge mode, config errors, low-level power)
- `custom_components/mabwarp/sensor_solar_forecast.py` - solar forecast values and dynamic plane discovery
- `custom_components/mabwarp/sensor_charge_limits.py` - charge limits timestamps and energy sensors
- `custom_components/mabwarp/sensor_misc.py` - features, info, charge manager, temperature, and P14A ENWG sensors
- `custom_components/mabwarp/number.py` - bidirectional charging current control
- `custom_components/mabwarp/button.py` - write-only start/stop buttons
- `custom_components/mabwarp/switch.py` - bidirectional user enable/disable


### Tests
- `tests/conftest.py` - shared fixtures (MockConfigEntry)
- `tests/test_config_flow.py` - config flow unit tests
- `tests/test_sensor.py` - sensor setup/integration tests (duplicate-ID check, discovery tasks)
- `tests/test_sensor_base.py` - base sensor class, coordinator, extract_field tests
- `tests/test_sensor_evse.py` - EVSE, meter, and NFC sensor tests
- `tests/test_sensor_charge_tracker.py` - charge tracker sensor tests
- `tests/test_sensor_power_manager.py` - power manager sensor tests
- `tests/test_sensor_solar_forecast.py` - solar forecast sensor tests
- `tests/test_sensor_charge_limits.py` - charge limits sensor tests
- `tests/test_sensor_misc.py` - misc sensor tests (features, temperature, P14A ENWG)
- `tests/test_number.py` - number entity unit tests
- `tests/test_button.py` - button entity unit tests
- `tests/test_switch.py` - switch entity unit tests


### Project config
- `pyproject.toml` - all project config: dependencies, pytest, ruff, coverage, pyright, mypy (version is `dynamic`, read from `manifest.json`; `.coveragerc` removed)
- `hacs.json` - HACS metadata
- `.gitignore` - standard Python + HA ignores


### Scripts
- `scripts/sync-manifest.ps1` - syncs version between manifest.json and pyproject.toml


### CI/CD
- `.github/workflows/ci.yaml` - pytest with coverage + ruff + HACS validation + hassfest on push (main)
- `.github/workflows/lint.yaml` - ruff lint + format check on push (main)
- `.github/workflows/validate.yaml` - HACS validation + hassfest on push (main)
- `.github/dependabot.yaml` - weekly pip + github-actions updates


---


## METER_VALUE_ID Correction History (Shelly 3EM Pro)

The `METER_VALUE_ID_*` constants in `const.py` were corrected based on the
official WARP API documentation and verified against Shelly 3EM Pro payloads:

| Sensor                      | WARP Value ID | Notes                        |
|-----------------------------|---------------|------------------------------|
| Voltage L1                  | 1             |                              |
| Voltage L2                  | 2             |                              |
| Voltage L3                  | 3             |                              |
| Current L1                  | 13            |                              |
| Current L2                  | 17            |                              |
| Current L3                  | 21            |                              |
| Power L1                    | 39            |                              |
| Power L2                    | 48            |                              |
| Power L3                    | 57            |                              |
| Power total                 | 74            |                              |
| Energy total                | 213           | TOTAL_INCREASING device class |

Source: https://docs.warp-charger.com/de/docs/interfaces/mqtt_http/api_reference/meters/

Additional optional values (not yet mapped):
- 33 (Summe Strom), 154 (Summe Scheinleistung), 209/211 (Wirkenergie Bezug/Einspeisung),
  357-359 (Leistungsfaktor je Phase).


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
| meters/{slot}/values   | ❌    | ✅        | 🔍 verify  |
| nfc/last_seen          | ✅    | ✅        | 🔍 verify  |
| charge_manager/state   | ✅    | ✅        | 🔍 verify  |

> ⚠️ `meter/values` is the legacy single-meter API (values are null if no direct meter attached).
> WARP3+ uses `meters/{slot}/values` where slot is typically `1` for the first external meter (e.g. Shelly Pro 3EM via Modbus TCP).
> The slot is currently hardcoded to `1` in `const.py`.


---


## Running Tests Locally
```powershell
uv sync --dev --extra dev
uv run pytest tests/ -v --cov=custom_components.mabwarp --cov-report=term-missing
```


## Running Linter Locally
```powershell
ruff check custom_components/mabwarp/ tests/
ruff format --check custom_components/mabwarp/ tests/
pre-commit run --all-files
```


---


## Release Process
1. Update `version` in `custom_components/mabwarp/manifest.json` - this is the single source of truth
2. Update `CHANGELOG.md`
3. Commit auf `main`
4. Create GitHub Release with tag `vX.Y.Z` matching the version
5. HACS picks up the new release automatically

> ℹ️ `pyproject.toml` reads the version dynamically from `manifest.json` via `get_version.py` (hatchling).
> Never edit the version in `pyproject.toml` directly.


---


## TODO / Open Items
- [ ] Verify WARP4 topic compatibility
- [ ] Make meter slot configurable (currently hardcoded to slot 1 in const.py)
- [ ] Verify correct array index mapping for meters/values per WARP version
- [ ] Add select entity for charge mode
- [ ] Add energy dashboard support (long-term statistics)
- [ ] Write integration tests with mocked MQTT broker
- [ ] Submit to HACS default repository once stable
