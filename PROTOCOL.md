# VapourFlow / Autostat Bluetooth protocol notes

Worked out by Claude (Anthropic's AI) in November 2026 from the Android app `com.softuvo.vapourflow` v1.0 and confirmed against a WAD 150 (firmware `Autostat8d_stm32l100rb_v8.4.7a`). Anything marked *unconfirmed* is read from the app's code but has not been tested on a real fan.

## Radio

- Bluetooth Low Energy module: Microchip **RN4020**.
- Advertises service UUID `4155544f-5354-4154-8943-5f5f30303031` (ASCII "AUTOSTAT…0001"). No pairing or bonding is needed.
- Accepts one connection at a time. The range is short, so use a proxy close by.

## Characteristics

All share the prefix `524e3430-3230-4f56-812e-`. The last six bytes spell the name in ASCII.

| Name | UUID suffix | Properties | Use |
|---|---|---|---|
| ON32 (app: OS32) | `305f4f4e3332` | read | Status flags (4 bytes) |
| ON64 (app: OS64) | `305f4f4e3634` | read | Live readings (8 bytes); empty until the login + check-now writes |
| IE64 | `305f49453634` | write | Login (`"123456"` ASCII) / EEPROM data in |
| IOE08 | `30494f453038` | read, write | 1 = "check now" / EEPROM busy flag |
| IT32 | `305f49543332` | write | 32-bit command register (*unconfirmed*) |
| IE32 | `305f49453332` | write | EEPROM command word (*unconfirmed*) |
| OE64 | `305f4f453634` | read | EEPROM data out |
| OT08 | `305f4f543038` | read | Single byte; matched the temperature in testing |
| OH16 | `305f4f483136` | read | Unknown |

## Reading live values

1. Write `123456` (ASCII bytes) to IE64 with response.
2. Wait about 2 s, then write `0x01` to IOE08 with response.
3. Wait about 2 s, then read ON32 and ON64.

The app does steps 1 and 2 on every connect (`setPassword`, `checkNow`). It also writes the current date and time (*unconfirmed*); this integration doesn't.

### ON64 (8 bytes)

Example: `14 15 2c 2d 04 5e 04 5f`

- byte 1: temperature °C, signed (`0x15` = 21)
- byte 3: relative humidity % (`0x2d` = 45)
- bytes 0 and 2 look like a second temperature/humidity pair. Bytes 4–7 are unknown. The app only uses bytes 1 and 3.

### ON32 (4 bytes)

| Byte | Bits | Meaning |
|---|---|---|
| 0 | `0x01` | Alarm |
| 0 | `0x02` | Dehumidify on |
| 0 | `0xF8` (>>3) | "External air" value |
| 1 | `0x40` | Fan speed (boost) |
| 1 | `0x80` | Fan direction: 1 = intake, 0 = extract |
| 2 | `0x01` | Test acknowledge |
| 2 | `0x04` | Smoke extract |
| 2 | `0x08` | Heater on |
| 2 | `0x70` (>>4) | Application version |
| 2 | `0x80` | Sounder |
| 3 | `0x01` | Opto-isolator (light switch input) |
| 3 | `0x02` | Override |
| 3 | `0x04` | Smoke detected |
| 3 | `0x08` | Heat detected |
| 3 | `0x10` | Flap/valve |
| 3 | `0x20` | Power supply (polarity unconfirmed) |
| 3 | `0xC0` (>>6) | Battery (meaning unconfirmed) |

There is **no "motor running" bit**.

## Commands (*unconfirmed, not used by this integration*)

IT32 is a 32-bit register that mirrors the state. The app starts from the ON32 state, clears some alarm/log bits, sets the field, then writes the value as big-endian bytes with leading zero bytes dropped.

| Mask | Meaning |
|---|---|
| `0x00800000` | Fan direction (1 = intake) |
| `0x00400000` | Fan speed (boost) |
| `0x02000000` | Dehumidification on |
| `0x00008000` | Heater control |
| `0x00007F00` | Humidity set level |

## EEPROM reads (*unconfirmed, not used*)

The settings, logs, serial number and counters live in the fan's memory. The app reads them like this:

1. Write `0` to IOE08.
2. Write a command word to IE32: address in `0x0001FFFF`, length in `0xFFF00000`, write flag `0x00020000` = 0, read flag `0x00040000` = 1.
3. Poll IOE08 until it reads 0.
4. Read the data from OE64.

Known addresses from the app: 47 (length 2) is a temperature value ("readSmokeTemp"), 35 or 188 (length 12) is the humidity settings, and 0 (length 3) is the smoke/humidity data. Getting a bit wrong here could write to the EEPROM, so be careful.
