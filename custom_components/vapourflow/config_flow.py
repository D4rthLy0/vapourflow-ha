from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS
import voluptuous as vol

from .const import DOMAIN, SERVICE_UUID


class VapourFlowConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._address: str | None = None

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak):
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._address = discovery_info.address
        self.context["title_placeholders"] = {"name": "VapourFlow fan"}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="VapourFlow fan", data={CONF_ADDRESS: self._address})
        return self.async_show_form(step_id="confirm", description_placeholders={"address": self._address})

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="VapourFlow fan", data=user_input)
        found = [i.address for i in async_discovered_service_info(self.hass)
                 if SERVICE_UUID in [u.lower() for u in i.service_uuids]]
        if not found:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(found)}))
