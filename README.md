# VapourFlow fan for Home Assistant (unofficial)

> 🚧 **Work in progress, parked (13 Nov 2026): temperature and humidity are NOT live.** The values read from the fan never change, so the "21 °C / 45 %" shown is a stored value, not a measurement. Don't rely on these two sensors, or on the status flags, which haven't been seen to change either. See [What we've tried](#what-weve-tried-so-far) below. The project is on hold until we can see how the newer iOS app gets live readings.

A Home Assistant custom integration that reads a **VapourFlow** ventilation fan (tested on a **WAD 150**) over Bluetooth, the same way the VapourFlow app does. No cloud, no app needed once it is set up.

> 🤖 **Built with AI.** This integration and the protocol notes were produced by **Claude (Anthropic's AI, via Claude Code)** working with the owner of the fan in November 2026. The AI decompiled the old Android app to learn the Bluetooth protocol, wrote the code and tested it against a real fan. A human checked each step and noted down the fan's settings first, but please treat it as experimental and review it before you rely on it.

> ⚠️ **Unofficial.** Not made by, endorsed by or connected to VapourFlow. Use at your own risk.

## What you get

| Entity | Notes |
|---|---|
| Temperature (°C) | ⚠️ Not live yet: shows a fixed value (see the warning above) |
| Humidity (%RH) | ⚠️ Not live yet: shows a fixed value (see the warning above) |
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
3. Reads `ON32` (status flags) and `ON64` (thought to be temperature + humidity, but see the warning at the top), then disconnects.

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

No settings were changed at any point, and the integration has never sent an EEPROM command.

### The challenges

- **Only the old app's code is available.** The Android app (v1.0) is no longer on Google Play and crashes when it connects. The working app is the iOS version (v2.0), and its code can't easily be inspected. The fan's firmware is `v8.4.7a`, which may expect the newer app's behaviour.
- **The old app never asks for live readings.** In v1.0, live temperature and humidity only come from `ON64` (byte 1 and byte 3, exactly as this integration reads them), but nothing in that app actively requests them. The v2.0 app must do an extra step we can't see.
- **Guessing is risky.** The fan's memory read and write commands differ by a single bit. A wrong guess could overwrite a setting in the fan's permanent memory, so we won't experiment blindly.
- **One connection at a time, weak radio.** The fan accepts only one Bluetooth connection, so the app and Home Assistant can't both be connected, and it often drops readings through walls.

### Next step (when resumed)

Record the iOS app's Bluetooth conversation with Apple's **PacketLogger** (part of *Additional Tools for Xcode*, on a Mac) using the iOS Bluetooth logging profile, while the app's dashboard shows live readings. A cheap BLE sniffer (e.g. an nRF52840 dongle with nRF Sniffer and Wireshark) would also work. Both only listen, so the fan's settings are never at risk. The recording should show exactly which writes make the fan report live values.

If you own a VapourFlow fan and a Mac, a PacketLogger trace would help a lot. Please open an Issue.

## Requirements

- Home Assistant with working Bluetooth: a local adapter or an **ESPHome Bluetooth proxy** near the fan. The fan's radio is weak, so a proxy in the same room helps a lot.
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
