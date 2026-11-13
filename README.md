# VapourFlow fan for Home Assistant (unofficial)

> ✅ **Update 13 Nov 2026: live readings work, through an ESPHome Bluetooth proxy.** Earlier versions of this page said the temperature and humidity weren't live. That turned out to depend on **which Bluetooth adapter Home Assistant uses**. Through the host's own Bluetooth adapter (BlueZ), the fan kept returning a frozen snapshot. Through an **ESPHome Bluetooth proxy** (an M5Stack Atom Lite about 3 m from the fan), the same reads are live: humidity rose from 45 % to 58 % within two minutes of boiling a kettle under the fan, and the intake/extract and boost flags followed what the fan was doing. See [What we've tried](#what-weve-tried-so-far). Still experimental: please report your results.

A Home Assistant custom integration that reads a **VapourFlow** ventilation fan (tested on a **WAD 150**) over Bluetooth, the same way the VapourFlow app does. No cloud, no app needed once it is set up.

> 🤖 **Built with AI.** This integration and the protocol notes were produced by **Claude (Anthropic's AI, via Claude Code)** working with the owner of the fan in November 2026. The AI decompiled the old Android app to learn the Bluetooth protocol, wrote the code and tested it against a real fan. A human checked each step and noted down the fan's settings first, but please treat it as experimental and review it before you rely on it.

> ⚠️ **Unofficial.** Not made by, endorsed by or connected to VapourFlow. Use at your own risk.

## What you get

| Entity | Notes |
|---|---|
| Temperature (°C) | Live through an ESPHome proxy (see the note above) |
| Humidity (%RH) | Live through an ESPHome proxy (see the note above) |
| Heater | On/off (the 200 W heater only runs in intake mode in cold weather) |
| Intake mode | On = intake (fresh air in), off = extract |
| Boost, Dehumidify | On/off |
| Alarm, Smoke detected, Heat detected, Sounder | Fault/alarm flags |
| Light switch input, Override | Status inputs |
| Power supply flag, Battery code, External air value, Valve flag | Diagnostic: raw values whose meaning isn't confirmed |

It polls every 2 minutes. If one reading fails it retries after 10 s, and it keeps the last good readings for up to 30 minutes before going unavailable.

**It does not control the fan.** It never sends settings and never touches the fan's memory (see below).

## What it sends to the fan

Each poll it repeats exactly what the official app does every time it connects, then reads:

1. Writes the app's fixed login `123456` to the `IE64` characteristic.
2. Writes `0x01` to `IOE08` ("check now"). Without these two steps the temperature/humidity value comes back empty.
3. Reads `ON32` (status flags) and `ON64` (temperature + humidity), then disconnects.

## What we've tried so far

| Date (2026) | What we did | Result |
|---|---|---|
| 11 Nov | Decompiled the old Android app (v1.0) to learn the Bluetooth protocol | Characteristics, status flags and command bits decoded (see [PROTOCOL.md](PROTOCOL.md)) |
| 11 Nov | Plain reads of `ON32` / `ON64` | `ON64` came back empty |
| 11 Nov | Sent the app's login (`123456` to `IE64`) and "check now" (`IOE08` = 1) first | `ON64` filled in: `14 15 2c 2d 04 5e 04 5f`, which looked like 21 °C / 45 % |
| 12 Nov | Logged about 390 reads over a day | Every read returned exactly the same bytes, so they aren't live |
| 12 Nov | Also read `OT08` and `OH16` each poll | Also fixed: `15` and `1b92` |
| 13 Nov | Boiled a kettle under the fan | The fan reacted (its light went amber, then green), but every value read stayed the same, including the status flags in `ON32` |
| 13 Nov | At the same moment, the iOS app (v2.0) showed live values: 47 %RH, 23 °C, outside air 24 °C | So the fan does have live readings; we just don't fetch them the same way |
| 13 Nov | Checked the planned memory (EEPROM) read before sending it | Stopped before sending anything: the "humidity" memory read (address 35, 12 bytes) returns the dynamic humidity **thresholds**, not live humidity |
| 13 Nov | Noticed the frozen values changed once, straight after the iOS app had connected, then froze again | The values looked like a snapshot refreshed only by the app |
| 13 Nov | Plugged in an ESPHome Bluetooth proxy (M5Stack Atom Lite) about 3 m from the fan; Home Assistant started connecting through it | **Every read became live.** Over 3 minutes held connected, temperature went 19 → 22 °C and humidity 44 → 37 % (after an earlier kettle), and `ON32` showed intake + boost |
| 13 Nov | Second kettle test, reading every 10 s through the proxy | Humidity 45 → 58 % within about 2½ minutes; the fan switched to extract + boost, and `ON32` showed it. Normal 2-minute polls are live too |

No settings were changed at any point, and the integration has never sent an EEPROM command.

### What we learned

- **Use an ESPHome Bluetooth proxy near the fan.** Through the host's own adapter (a MediaTek MT7922 passed through to a Home Assistant OS VM, using BlueZ), reads kept returning the same snapshot. Through the proxy they're live. We don't know why yet: it might be BlueZ caching, or how the fan's RN4020 Bluetooth module behaves with different connections. Reports from other setups are welcome.
- **No extra commands are needed.** The login (`123456` to `IE64`) and "check now" (`IOE08` = 1) the app sends on connect are enough. No EEPROM access is involved.
- **The fan's radio is weak.** Even 3 m away with a clear view, the proxy only sees it at about −90 dBm, but connections still work. Mounting the proxy high up, with a clear view of the fan, helped.

### Still unknown

- The meaning of `ON32` byte 0 bits 3–7 (the app calls it "external air") and of `OT08` / `OH16`, which both change but aren't decoded.
- Why the host adapter returned stale values.

## Requirements

- Home Assistant with an **ESPHome Bluetooth proxy** near the fan (strongly recommended). A local adapter may connect, but in our testing it returned frozen values (see above). The fan's radio is weak, so put the proxy in the same room, high up, with a clear view of the fan.
- The fan only accepts **one connection at a time**. Close the VapourFlow app before Home Assistant polls, or temporarily disable this integration while you use the app.

## Install

**HACS (custom repository):** HACS → ⋮ → Custom repositories → add `https://github.com/D4rthLy0/vapourflow-ha` as type *Integration*, install **VapourFlow**, restart Home Assistant.

**Manual:** copy `custom_components/vapourflow` into your `config/custom_components/` folder and restart.

The fan should then be discovered automatically (Settings → Devices & services). If not, add the **VapourFlow** integration and pick it from the list.

## Tested with

- VapourFlow WAD 150, firmware `Autostat8d_stm32l100rb_v8.4.7a`
- Home Assistant 2026.11

Other VapourFlow / "Autostat" models probably use the same protocol, but this is untested. Reports welcome in Issues.

## Useful links (official VapourFlow pages)

- [WAD warm air dehumidifier fan: product page](https://www.vapourflow.com/product/wad-warm-air-dehumidifier-fan-attic-whole-house/), with the [WAD datasheet (PDF)](https://www.vapourflow.com/wp-content/uploads/META-INLINE-WAD-01-2026.pdf)
- [VapourFlow app user guide](https://www.vapourflow.com/vapourflow-app-user-guide/), with the [guide as a PDF](https://www.vapourflow.com/wp-content/uploads/Vapourflow-App-User-Guide-1_22.pdf)
- [Installation](https://www.vapourflow.com/installation/)

These are VapourFlow's own documents, linked rather than copied.

## Protocol

See [PROTOCOL.md](PROTOCOL.md) for everything that was worked out, including the parts this integration doesn't use yet (commands, memory reads).
