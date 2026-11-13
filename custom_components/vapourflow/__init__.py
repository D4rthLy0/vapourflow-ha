"""VapourFlow WAD fan over Bluetooth (read-only for now)."""
from __future__ import annotations

import asyncio
import time
from datetime import timedelta
import logging

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CHAR_IE64, CHAR_IOE08, CHAR_ON32, CHAR_ON64, DOMAIN, UPDATE_SECONDS

STALE_AFTER = 30 * 60  # keep showing the last readings for up to 30 min of failed polls

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


def parse(on32: bytes, on64: bytes) -> dict:
    """Turn the raw status bytes into readings (layout from the app's parseOS32/parseOS64)."""
    data: dict = {"raw_on32": on32.hex(), "raw_on64": on64.hex()}
    if len(on64) > 1:
        data["temperature"] = int.from_bytes(on64[1:2], "little", signed=True)
    if len(on64) > 3:
        data["humidity"] = on64[3]
    if len(on64) > 7:
        # Water vapour pressure in pascals (bytes 6-7, big-endian; bytes 4-5 are a near-identical
        # second copy). Checked 2026-11-13: 21 °C/45 % -> 1119 Pa, 19 °C/43 % -> 945 Pa.
        data["vapour_pressure"] = int.from_bytes(on64[6:8], "big")
    if len(on32) > 2:
        data["dehumidify_on"] = bool(on32[0] & 0x02)
        data["boost"] = bool(on32[1] & 0x40)
        data["intake"] = bool(on32[1] & 0x80)  # 1 = intake (warm fresh air in), 0 = extract
        data["heater"] = bool(on32[2] & 0x08)
        data["alarm"] = bool(on32[0] & 0x01)
        data["external_air"] = (on32[0] & 0xF8) >> 3
        data["sounder"] = bool(on32[2] & 0x80)
    if len(on32) > 3:
        b3 = on32[3]
        data["light_switch"] = bool(b3 & 0x01)     # optoisolator input
        data["override"] = bool(b3 & 0x02)
        data["smoke_detected"] = bool(b3 & 0x04)
        data["heat_detected"] = bool(b3 & 0x08)
        data["valve_flag"] = (b3 & 0x10) >> 4
        data["power_supply_flag"] = (b3 & 0x20) >> 5  # meaning of 0/1 not confirmed yet
        data["battery_code"] = (b3 & 0xC0) >> 6       # meaning not confirmed yet
    return data


class VapourFlowCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, address: str) -> None:
        super().__init__(hass, _LOGGER, name=f"VapourFlow {address}",
                         update_interval=timedelta(seconds=UPDATE_SECONDS))
        self.address = address
        self._last: dict | None = None
        self._last_ok = 0.0

    async def _read_once(self) -> dict:
        device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if device is None:
            raise UpdateFailed("Fan not in Bluetooth range right now")
        client = await establish_connection(BleakClientWithServiceCache, device, "VapourFlow", max_attempts=3)
        try:
            # Same two messages the app sends on every connect (setPassword, checkNow).
            # No settings, no EEPROM access.
            await client.write_gatt_char(CHAR_IE64, b"123456", response=True)
            await asyncio.sleep(2)
            await client.write_gatt_char(CHAR_IOE08, b"\x01", response=True)
            await asyncio.sleep(2)
            on32 = bytes(await client.read_gatt_char(CHAR_ON32))
            on64 = bytes(await client.read_gatt_char(CHAR_ON64))
        finally:
            await client.disconnect()
        return parse(on32, on64)

    async def _async_update_data(self) -> dict:
        """Read the fan; the Bluetooth link is weak, so retry once and ride out short gaps."""
        last_err: Exception | None = None
        for attempt in (1, 2):
            try:
                data = await self._read_once()
                if "humidity" not in data:
                    raise UpdateFailed("Fan answered without temperature/humidity")
                self._last = data
                self._last_ok = time.monotonic()
                _LOGGER.debug("VapourFlow read: %s", data)
                return data
            except Exception as err:  # noqa: BLE001
                last_err = err
                if attempt == 1:
                    await asyncio.sleep(10)
        if self._last is not None and time.monotonic() - self._last_ok < STALE_AFTER:
            _LOGGER.info("VapourFlow read failed (%s); keeping last readings", last_err)
            return self._last
        raise UpdateFailed(f"Bluetooth read failed: {last_err}") from last_err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = VapourFlowCoordinator(hass, entry.data[CONF_ADDRESS])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
