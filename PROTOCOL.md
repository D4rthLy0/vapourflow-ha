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

Decoded twice, independently, from the app's `AutostatOperations` (`setFanIntake`, `setDehumidication`, `setHumidifcation`, `setAlarm`). Nothing here has been sent to a real fan yet.

IT32 is a 32-bit register. To send a command, the app:

1. Starts from its copy of the state. On every ON32 read it copies two bits across: boost `0x00400000` from ON32 byte 1 `0x40`, and direction `0x00800000` from ON32 byte 1 `0x80`.
2. Clears the one-shot bits: `0x80000000`, `0x40000000`, `0x30000000`, `0x08000000`, `0x00200000`, `0x00100000`, `0x2000`, `0x1000` and `0x0100`.
3. Sets the field for the command (see the table).
4. Writes the value to IT32 with response, as **unsigned hex with leading zero bytes dropped, big-endian**. For example, `0x00800000` is sent as `80 00 00`, `0x04800000` as `04 80 00 00`, and `0` as `00`.

To confirm a command worked, write `0x01` to IOE08, wait about 2 s, then read ON32 again.

| Mask | Meaning |
|---|---|
| `0x00800000` | Fan direction (1 = intake, 0 = extract) |
| `0x00400000` | Fan speed (boost). The app only copies this from ON32 and never sets it, so boost seems to be automatic |
| `0x04000000` | `setDehumidication` (0/1) |
| `0x02000000` | `setHumidifcation` (0/1). Probably matches ON32 byte 0 `0x02` |
| `0x80000000` | `setAlarm` (one-shot) |

The app does **not** copy the `0x04000000` and `0x02000000` bits from ON32, so a direction change after an app restart sends them as 0. It is probably safer to copy them from ON32 byte 0 (`0x04` and `0x02`) as well.

**Do not send** these bits. They are listed only so they can be avoided:

| Mask | Meaning |
|---|---|
| `0x00000200` | Bootloader mode |
| `0x00000400` | Smoke extract |
| `0x01000000` | Fan test |
| `0x00080000` | Flap test |
| `0x00010000` | Heater test |
| `0x00008000` | Heater control |
| `0x00007F00` | Humidity set level |
| `0x10000000` | One-hour log |
| `0x08000000` | Battery log |

## EEPROM settings writes (*unconfirmed, risky, not used*)

Fan speed % (`setSpeedPercentage`, 0–100) and the humidity threshold (`setHumidityLevel`, 0–99) are stored settings, not IT32 bits. The app writes them like this:

1. Write `0x00` to IOE08.
2. Write a command word to IE32: the address, plus count `1 << 20`, plus write flag `0x00020000`, plus start flag `0x00040000`.
3. Send the data byte.
4. Write `0x01200000` to IT32 to commit.

Addresses: speed `0xB2`, `0xB3`, `0xB5` and `0xB6`; humidity `0xB8` and `0xB9`. The wrong address writes the wrong setting into the fan's permanent memory.

## EEPROM reads (*unconfirmed, not used*)

The settings, logs, serial number and counters live in the fan's memory. The app reads them like this:

1. Write `0` to IOE08.
2. Write a command word to IE32: address in `0x0001FFFF`, length in `0xFFF00000`, write flag `0x00020000` = 0, read flag `0x00040000` = 1.
3. Poll IOE08 until it reads 0.
4. Read the data from OE64.

Known addresses from the app: 47 (length 2) is a temperature value ("readSmokeTemp"), 35 or 188 (length 12) is the humidity settings, and 0 (length 3) is the smoke/humidity data. Getting a bit wrong here could write to the EEPROM, so be careful.
