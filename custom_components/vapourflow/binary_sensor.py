from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity import VapourFlowEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([
        VFBinary(c, "heater", "Heater", BinarySensorDeviceClass.HEAT, "mdi:radiator"),
        VFBinary(c, "intake", "Intake mode", None, "mdi:home-import-outline"),
        VFBinary(c, "boost", "Boost", None, "mdi:fan-plus"),
        VFBinary(c, "dehumidify_on", "Dehumidify", None, "mdi:water-percent"),
        VFBinary(c, "alarm", "Alarm", BinarySensorDeviceClass.PROBLEM, "mdi:alert"),
        VFBinary(c, "smoke_detected", "Smoke detected", BinarySensorDeviceClass.SMOKE, None),
        VFBinary(c, "heat_detected", "Heat detected", BinarySensorDeviceClass.HEAT, "mdi:fire-alert"),
        VFBinary(c, "sounder", "Sounder", BinarySensorDeviceClass.SOUND, None),
        # ON32 byte 3 bit 0: the pull cord on the unit (confirmed 2026-11-13). On = forced extract + boost
        # (red LED); pull again for automatic. The app calls it the light switch trigger input.
        VFBinary(c, "light_switch", "Pull cord (forced extract)", None, "mdi:gesture-tap"),
        VFBinary(c, "override", "Override", None, "mdi:hand-back-right"),
    ])


class VFBinary(VapourFlowEntity, BinarySensorEntity):
    def __init__(self, c, key, name, dc, icon):
        super().__init__(c, key, name)
        self._attr_device_class = dc
        self._attr_icon = icon

    @property
    def is_on(self):
        return self.coordinator.data.get(self._key)
