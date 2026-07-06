# mABwarp
Bridges Tinkerforge WARP Charger MQTT topics to Home Assistant – the Auto Discovery it deserves

## Supported Features

### EVSE & Meter Values
- IEC61851 state, charger state, allowed charging current, error state
- CP PWM duty cycle, uptime
- Voltage/current/power per phase and total (L1/L2/L3)
- Energy total (kWh, TOTAL_INCREASING)

### Charge Manager
- Charge manager state
- Allocated current slots (0-3)

### Power Manager
- Charge mode (Standby/Min/PV/Min+PV)
- Power manager state and low-level state
- Config error flags

### Charge Tracker
- Tracked charges count
- Current charge meter start
- Current charge user ID
- Last charge (energy, duration, user, timestamp)

### Solar Forecast
- Solar forecast values (wh_today, wh_today_remaining, wh_tomorrow)
- Solar plane discovery (dynamic plane count)

### Charge Limits
- Start/target timestamp
- Start/target energy

### Temperatures
- Current temperature
- Dynamic temperature key discovery

### P14A ENWG
- Throttling status (binary)
- Maximum allowed power

### Day Ahead Prices (optional, hardwareabhängig)
- Current day ahead price (ct/kWh)
- Price forecast array with extra state attributes

## TODO
- network/wifi Diagnose-Sensoren (Signalstärke, Verbindungsstatus) — geplant für spätere Version.
- Energy-Dashboard-Support
