from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature

from .entity import VapourFlowEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([
        VFSensor(c, "temperature", "Temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
        VFSensor(c, "humidity", "Humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
        VFDiag(c, "power_supply_flag", "Power supply flag", "mdi:power-plug"),
        VFDiag(c, "battery_code", "Battery code", "mdi:battery-unknown"),
        VFDiag(c, "external_air", "External air value", "mdi:weather-windy"),
        VFDiag(c, "valve_flag", "Valve flag", "mdi:valve"),
    ])


class VFSensor(VapourFlowEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, c, key, name, dc, unit):
        super().__init__(c, key, name)
        self._attr_device_class = dc
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data or {}
        return {"raw_on32": d.get("raw_on32"), "raw_on64": d.get("raw_on64")}


class VFDiag(VapourFlowEntity, SensorEntity):
    """Raw status values whose exact meaning isn't confirmed yet (shown under Diagnostic)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c, key, name, icon):
        super().__init__(c, key, name)
        self._attr_icon = icon

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)
