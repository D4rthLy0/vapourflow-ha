# VapourFlow fan for Home Assistant (unofficial)

A Home Assistant custom integration that reads a **VapourFlow** ventilation fan (tested on a **WAD 150**) over Bluetooth, the same way the VapourFlow app does. No cloud, no app needed once it is set up.

> 🤖 **Built with AI.** This integration and the protocol notes were produced by **Claude (Anthropic's AI, via Claude Code)** working with the owner of the fan in November 2026. The AI decompiled the old Android app to learn the Bluetooth protocol, wrote the code and tested it against a real fan. A human checked each step and backed up the fan's settings first, but please treat it as experimental and review it before you rely on it.

> ⚠️ **Unofficial.** Not made by, endorsed by or connected to VapourFlow. Use at your own risk.

## What you get

| Entity | Notes |
|---|---|
| Temperature (°C) | Live, from the fan's own sensor |
| Humidity (%RH) | Live, from the fan's own sensor |
| Heater | On/off (the 200 W heater only runs in intake mode in cold weather) |
| Intake mode | On = intake (fresh air in), off = extract |
| Boost, Dehumidify | On/off |
| Alarm, Smoke detected, Heat detected, Sounder | Fault/alarm flags |
| Light switch input, Override | Status inputs |
| Power supply flag, Battery code, External air value, Valve flag | Diagnostic: raw values whose meaning isn't confirmed |

It polls every 5 minutes. If one reading fails it retries after 10 s, and it keeps the last good readings for up to 30 minutes before going unavailable.

**It does not control the fan.** It never sends settings and never touches the fan's memory (see below).

## What it sends to the fan

Each poll it repeats exactly what the official app does every time it connects, then reads:

1. Writes the app's fixed login `123456` to the `IE64` characteristic.
2. Writes `0x01` to `IOE08` ("check now"). Without these two steps the temperature/humidity value comes back empty.
3. Reads `ON32` (status flags) and `ON64` (temperature + humidity), then disconnects.

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
