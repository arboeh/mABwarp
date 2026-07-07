# .kilocode/rules/ha-review-policy.md

## Aktivierung
Bei jedem PR/Diff in `custom_components/mabwarp/**` automatisch beide Skills laden:
- ha-python-clean-reviewer (Compliance-Gate, Severity-Gate: high)
- home-assistant-best-practices (nur bei Änderungen an automations/dashboards - hier meist nicht relevant für Custom Component)

## Projekt-spezifische Overrides (reviewer_config)

reviewer_config:
  ha_core_min_version: "2026.6"
  python_min_version: "3.12"
  review_scope: "diff"
  fail_on_severity: "high"
  enforce_async_strictness: true
  enforce_typing: true
  enforce_clean_code: true
  style_guide: "google"
  style_enforce_level: "medium"
  target_paths:
    - "custom_components/mabwarp/**"
  exclude_paths:
    - "tests/fixtures/**"

## Projekt-spezifische Regeln (zusätzlich zur Standard-Checkliste)

1. **Basisklasse statt Duplikation**: Neue Entity-Klassen MÜSSEN von einer
   gemeinsamen Basisklasse mit device_info/unique_id-Helper erben statt
   die Properties erneut zu implementieren. PRs, die device_info erneut
   duplizieren, sind als CC-CLEAN-001 zu flaggen (severity: high).

2. **Feature-Flags typisiert**: Neue Feature-String-Vergleiche
   (`"xyz" in features`) sind zu vermeiden. Stattdessen Literal/StrEnum
   aus einem zentralen Feature-Modul verwenden. PRs mit neuen rohen
   String-Vergleichen sind als PY-STYLE-001 zu flaggen (severity: medium).

3. **ASSUMPTION-Kommentare**: Unverifizierte Werte (wie CHARGE_MODE_MAP)
   müssen weiterhin mit `# ASSUMPTION` / `# TODO: verify` markiert bleiben,
   bis eine Verifikation gegen echte Hardware erfolgt ist. Kein PR darf
   ASSUMPTION-Markierungen ohne Verifikationsnachweis entfernen.

4. **Test-Policy**: Neue MQTT-Handler-Klassen benötigen mindestens einen
   Unit-Test mit echtem Payload-Fixture (kein `{"dummy": "x"}`), und
   perspektivisch einen Integrationstest mit dem HA-Test-Harness
   (siehe offenes TODO "integration tests with mocked MQTT broker").

5. **Manifest-Sync**: `manifest.json`-Feld "homeassistant" muss mit
   `ha_core_min_version` aus dieser Config übereinstimmen — Abweichung
   ist ein Finding HA-CONFIG-001 (severity: medium).

## Output
Review-Ausgabe im Standard-Markdown-Format des ha-python-clean-reviewer
Skills. `require_release_verdict: true` — jeder Review muss ein
Merge Gate Recommendation enthalten.