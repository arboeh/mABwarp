![Logo](images/heading.svg)

[🇬🇧 English](README.md) | 🇩🇪 **Deutsch**

## Home Assistant Integration für Tinkerforge WARP Charger

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=home-assistant)](https://www.home-assistant.io/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![release](https://img.shields.io/github/v/release/arboeh/mABwarp?display_name=tag)](https://github.com/arboeh/mABwarp/releases/latest)
[![codecov](https://codecov.io/gh/arboeh/mABwarp/branch/main/graph/badge.svg)](https://codecov.io/gh/arboeh/mABwarp)
[![CI](https://github.com/arboeh/mABwarp/workflows/CI/badge.svg)](https://github.com/arboeh/mABwarp/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/arboeh/mABwarp/blob/main/LICENSE)
[![maintained](https://img.shields.io/maintenance/yes/2026)](https://github.com/arboeh/mABwarp/graphs/commit-activity)
[![Tinkerforge](https://img.shields.io/badge/Tinkerforge-WARP3-005B96)](https://www.tinkerforge.com/de/doc/Hardware/WARP3/WARP3.html)
[![MQTT](https://img.shields.io/badge/MQTT-based-660066?logo=mqtt)](https://mqtt.org)

> **⚠️ Release 1.0.0** - mABwarp ist produktionsreif, aber neu; bitte Probleme auf GitHub melden.

**mABwarp** bindet den [Tinkerforge WARP3 Charger](https://www.tinkerforge.com/de/doc/Hardware/WARP3/WARP3.html)
(EV-Wallbox) via MQTT in Home Assistant ein - vollständiger EVSE-Status,
Zählerwerte, Ladesteuerung und Diagnose direkt in der UI.

## Funktionen

- 🔌 **EVSE-Status** - Ladegerätzustand, Steckerstatus, Ladezustand als Sensoren
- ⚡ **Zählerwerte** - Spannung, Strom, Leistung und Energie pro Phase (verifiziert für Shelly 3EM Pro)
- 📊 **Charge Tracker** - Ladehistorie und Statistiken pro Ladevorgang
- 🎛️ **Charge Limits** - konfigurierbar über Number/Select-Entities
- 💶 **Day-Ahead-Preise** - Sensoren für dynamische Strompreise
- ☀️ **Solar Forecast** - PV-Prognose-Integration für intelligentes Laden
- 🧠 **Power Manager** - Lastmanagement und Prioritätssteuerung
- 🌐 **Netzwerk- & Firmware-Info** - Diagnose-Sensoren für den Charger
- 🔘 **Buttons** - Steuerungsaktionen als HA-Button-Entities
- 🛠️ **Config Flow mit Auto-Erkennung** - Features werden bei Setup automatisch via MQTT erkannt
- **🧪 Umfangreiche Testabdeckung**
  - Unit-Tests für **Config Flow, Sensoren, Number, Select, Button**
  - Regressionstests für Thread-Safety, fehlende Meter-Indizes, doppelte Unique-IDs, geänderte value_id-Reihenfolge
  - CI-Tests für **Python 3.12/3.13**

## Voraussetzungen

- Home Assistant **2026.3+** (für lokale Brand-Assets-Unterstützung)
- Tinkerforge **WARP3 Charger**, Firmware **2.12.0+6a3d2525** oder neuer
- MQTT-Broker in Home Assistant konfiguriert (`homeassistant.components.mqtt`)
- Charger im lokalen Netzwerk via MQTT erreichbar

## Unterstützte Geräte

| Gerät                     | Modell | Firmware          | Status     |
| -------------------------- | ------ | ------------------ | ---------- |
| ✅ **Tinkerforge WARP3**  | WARP3  | 2.12.0+6a3d2525+   | **Getestet** |
| 🟡 **Tinkerforge WARP2**  | WARP2  | -                   | Ungetestet |

**Zähler-Kompatibilität:**

| Zähler                   | Status                  |
| ------------------------- | ------------------------ |
| ✅ **Shelly 3EM Pro**    | **Getestet/Verifiziert** |
| 🟡 Andere WARP-unterstützte Zähler | Ungetestet (value_ids können abweichen) |

> **✅ Getestet**<br>
> **🟡 Ungetestet**: sollte laut WARP-API funktionieren, Community-Tests willkommen<br>
> **Gerät fehlt -> [Issue erstellen](https://github.com/arboeh/mABwarp/issues/new)**

## Screenshots

<!-- TODO: Screenshots aus laufender HA-Instanz erstellen und hier einbinden -->

### ![Brand Auswahl](images/select_brand.png)<br>

**Brand-Erkennung**<br>
mABwarp erscheint in der Geräte-Herstellerliste

### ![Setup](images/setup.png)<br>

**Setup-Flow**<br>
MQTT-Basistopic des WARP-Chargers eingeben → automatische Feature-Erkennung

### ![Gerät erstellt](images/device_created.png)<br>

**Integration bereit**<br>
Entities werden automatisch basierend auf erkannten Features angelegt

### ![Übersicht](images/device_overview.png)<br>

**Geräte-Übersicht**<br>
Hinzugefügter WARP-Charger

### ![Sensor-Übersicht](images/sensor_overview.png)<br>

**Sensor-Übersicht**<br>
EVSE-Status, Zählerwerte, Charge Tracker und Diagnose

## Installation via HACS

1. HACS öffnen → **Integrationen**
2. Auf **⋮ → Benutzerdefinierte Repositories** klicken
3. `https://github.com/arboeh/mABwarp` als Typ **Integration** hinzufügen
4. Nach **mABwarp** suchen und installieren
5. Home Assistant neu starten

## Manuelle Installation

1. `custom_components/mabwarp/` in den `config/custom_components/`-Ordner kopieren
2. Home Assistant neu starten

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **mABwarp** suchen
3. MQTT-Basistopic des WARP-Chargers eingeben
4. Features (Meter, Chargetracker, Chargelimits, Day-Ahead-Preise,
   Power Manager, Solar Forecast, NFC) werden automatisch via MQTT erkannt

## Entities

<!-- TODO: Tabelle mit tatsächlichen Entity-IDs aus sensor_*.py, number.py, select.py, button.py ergänzen -->

| Entity-Gruppe         | Typ                  | Beschreibung                          |
| ----------------------- | -------------------- | --------------------------------------- |
| EVSE-Status             | Sensor               | Lade-/Stecker-/Ladezustand              |
| Zählerwerte             | Sensor               | Spannung, Strom, Leistung, Energie      |
| Charge Tracker          | Sensor               | Ladehistorie und Statistiken            |
| Charge Limits           | Number/Select        | Konfigurierbare Ladelimits              |
| Day-Ahead-Preise        | Sensor               | Dynamische Strompreisdaten              |
| Power Manager           | Sensor               | Status des Lastmanagements              |
| Solar Forecast          | Sensor               | PV-Prognose für intelligentes Laden     |
| Netzwerk/Firmware       | Sensor (Diagnose)    | Verbindungs- und Firmware-Info          |

## Services

<!-- TODO: Tatsächlich registrierte Services aus __init__.py/services.yaml ergänzen -->

```yaml
service: mabwarp.<service_name>
data:
  device_id: "<device_id>"
```

## Bekannte Einschränkungen (1.0.0)

- Meter-value_id-Mapping nur für Shelly 3EM Pro verifiziert; andere Zähler erfordern ggf. Anpassung
- Keine Authentifizierung über die Standard-MQTT-Broker-Zugangsdaten hinaus

## Geplante Features (zukünftige Releases)

- 🔗 **Weitere Zähler-Unterstützung** - verifizierte value_id-Mappings für weitere Zählermodelle
- 📱 **Mobile Optimierung** - Lovelace-Cards für Ladeübersicht
- 🔐 **Erweiterte Diagnose** - tiefere Netzwerk-/Firmware-Einblicke

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md).

## Lizenz

MIT © 2026 [arboeh](https://github.com/arboeh) - siehe [LICENSE](LICENSE)
