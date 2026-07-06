![Logo](images/heading.svg)

🇬🇧 **English** | [🇩🇪 Deutsch](README.de.md)

## Home Assistant Integration for Tinkerforge WARP Charger

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=home-assistant)](https://www.home-assistant.io/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![release](https://img.shields.io/github/v/release/arboeh/mABwarp?display_name=tag)](https://github.com/arboeh/mABwarp/releases/latest)
[![codecov](https://codecov.io/gh/arboeh/mABwarp/branch/main/graph/badge.svg)](https://codecov.io/gh/arboeh/mABwarp)
[![CI](https://github.com/arboeh/mABwarp/workflows/CI/badge.svg)](https://github.com/arboeh/mABwarp/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/arboeh/mABwarp/blob/main/LICENSE)
[![maintained](https://img.shields.io/maintenance/yes/2026)](https://github.com/arboeh/mABwarp/graphs/commit-activity)
[![Tinkerforge](https://img.shields.io/badge/Tinkerforge-WARP3-005B96)](https://www.tinkerforge.com/de/doc/Hardware/WARP3/WARP3.html)
[![MQTT](https://img.shields.io/badge/MQTT-based-660066?logo=mqtt)](https://mqtt.org)

> **⚠️ Release 1.0.0** - mABwarp is production-ready but new; please report issues on GitHub.

**mABwarp** integrates the [Tinkerforge WARP3 Charger](https://www.tinkerforge.com/de/doc/Hardware/WARP3/WARP3.html)
(EV wallbox) into Home Assistant via MQTT - full EVSE status, metering, charge
control and diagnostics without leaving the UI.

## Features

- 🔌 **EVSE status** - charger state, plug status, charging state as sensors
- ⚡ **Meter values** - voltage, current, power and energy per phase (verified for Shelly 3EM Pro)
- 📊 **Charge Tracker** - per-session charge history and statistics
- 🎛️ **Charge Limits** - configurable via Number/Select entities
- 💶 **Day-Ahead Prices** - dynamic electricity pricing sensors
- ☀️ **Solar Forecast** - PV forecast integration for smart charging
- 🧠 **Power Manager** - load management and priority control
- 🌐 **Network & Firmware info** - diagnostic sensors for the charger
- 🔘 **Buttons** - control actions exposed as HA button entities
- 🛠️ **Config Flow with Auto-Detection** - features detected automatically via MQTT during setup
- **🧪 Extensive Test Coverage**
  - Unit tests for **config flow, sensors, number, select, button**
  - Regression tests for thread-safety, missing meter indices, duplicate unique IDs, changed value_id order
  - CI tests for **Python 3.12/3.13**

## Requirements

- Home Assistant **2026.3+** (for local brand assets support)
- Tinkerforge **WARP3 Charger**, Firmware **2.12.0+6a3d2525** or newer
- MQTT broker configured in Home Assistant (`homeassistant.components.mqtt`)
- Charger reachable via MQTT (local network)

## Supported Devices

| Device                    | Model  | Firmware        | Status     |
| -------------------------- | ------ | ---------------- | ---------- |
| ✅ **Tinkerforge WARP3**  | WARP3  | 2.12.0+6a3d2525+ | **Tested** |
| 🟡 **Tinkerforge WARP2**  | WARP2  | -                 | Untested   |

**Meter (energy meter) compatibility:**

| Meter                  | Status     |
| ----------------------- | ---------- |
| ✅ **Shelly 3EM Pro**  | **Tested/Verified** |
| 🟡 Other WARP-supported meters | Untested (value_ids may differ) |

> **✅ Tested**<br>
> **🟡 Untested**: should work per WARP API, community testing welcome<br>
> **Device missing -> [Create Issue](https://github.com/arboeh/mABwarp/issues/new)**

## Screenshots

<!-- TODO: Screenshots aus laufender HA-Instanz erstellen und hier einbinden -->

### ![Brand Selection](images/select_brand.png)<br>

**Brand Recognition**<br>
mABwarp appears in the device brand list

### ![Setup](images/setup.png)<br>

**Setup Flow**<br>
Enter your WARP charger's MQTT topic → automatic feature detection

### ![Device Created](images/device_created.png)<br>

**Integration Ready**<br>
Entities automatically created based on detected features

### ![Overview](images/device_overview.png)<br>

**Device Overview**<br>
Added WARP charger device

### ![Sensor Overview](images/sensor_overview.png)<br>

**Sensor Overview**<br>
EVSE status, meter values, charge tracker and diagnostics

## Installation via HACS

1. Open HACS → **Integrations**
2. Click **⋮ → Custom repositories**
3. Add `https://github.com/arboeh/mABwarp` as type **Integration**
4. Search for **mABwarp** and install
5. Restart Home Assistant

## Manual Installation

1. Copy `custom_components/mabwarp/` to your `config/custom_components/` folder
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **mABwarp**
3. Enter your WARP charger's MQTT base topic
4. Features (meters, chargetracker, chargelimits, dayaheadprices,
   powermanager, solarforecast, nfc) are auto-detected via MQTT

## Entities

<!-- TODO: Tabelle mit tatsächlichen Entity-IDs aus sensor_*.py, number.py, select.py, button.py ergänzen -->

| Entity Group        | Type                | Description                          |
| -------------------- | ------------------- | ------------------------------------- |
| EVSE Status          | Sensor              | Charger/plug/charging state           |
| Meter Values          | Sensor              | Voltage, current, power, energy       |
| Charge Tracker        | Sensor              | Session history and statistics        |
| Charge Limits         | Number/Select       | Configurable charging limits          |
| Day-Ahead Prices      | Sensor              | Dynamic electricity price data        |
| Power Manager         | Sensor              | Load management status                |
| Solar Forecast        | Sensor              | PV forecast for smart charging         |
| Network/Firmware      | Sensor (Diagnostic) | Connectivity and firmware info         |

## Services

<!-- TODO: Tatsächlich registrierte Services aus __init__.py/services.yaml ergänzen -->

```yaml
service: mabwarp.<service_name>
data:
  device_id: "<device_id>"
```

## Known Limitations (1.0.0)

- Meter value_id mapping verified only against Shelly 3EM Pro; other meters may require adjustment
- No authentication beyond standard MQTT broker credentials

## Planned Features (future releases)

- 🔗 **Additional meter support** - verified value_id mappings for more meter models
- 📱 **Mobile Optimization** - Lovelace cards for charge overview
- 🔐 **Extended diagnostics** - deeper network/firmware insights

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT © 2026 [arboeh](https://github.com/arboeh) - see [LICENSE](LICENSE)
