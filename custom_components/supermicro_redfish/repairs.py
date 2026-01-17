"""Repairs for Supermicro Redfish integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from aiosupermicro import SupermicroRedfishClient
from aiosupermicro.exceptions import AuthenticationError, ConnectionError
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_VERIFY_SSL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class ConnectionFailedRepairFlow(RepairsFlow):
    """Handler for connection failed repair flow."""

    def __init__(self, issue_id: str, data: dict[str, Any]) -> None:
        """Initialize the repair flow."""
        self._issue_id = issue_id
        self._entry_id = str(data.get("entry_id", ""))

    async def async_step_init(
        self, _user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the first step of the repair flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the confirm step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Get the config entry
            entry = self.hass.config_entries.async_get_entry(self._entry_id)
            if entry is None:
                return self.async_abort(reason="entry_not_found")

            # Test connection with provided credentials
            error = await self._async_test_connection(
                self.hass,
                {
                    CONF_HOST: entry.data[CONF_HOST],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_VERIFY_SSL: entry.data.get(CONF_VERIFY_SSL, False),
                },
            )

            if error:
                errors["base"] = error
            else:
                # Update credentials and reload
                new_data = {**entry.data, **user_input}
                self.hass.config_entries.async_update_entry(entry, data=new_data)
                await self.hass.config_entries.async_reload(self._entry_id)
                return self.async_create_entry(data={})

        # Get existing entry for placeholders
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        host = str(entry.data[CONF_HOST]) if entry else "unknown"

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={"host": host},
        )

    async def _async_test_connection(
        self, hass: HomeAssistant, data: dict[str, Any]
    ) -> str | None:
        """Test connection and return error key if failed."""
        session = async_get_clientsession(
            hass, verify_ssl=bool(data.get(CONF_VERIFY_SSL, False))
        )

        client = SupermicroRedfishClient(
            session=session,
            host=str(data[CONF_HOST]),
            username=str(data[CONF_USERNAME]),
            password=str(data[CONF_PASSWORD]),
            verify_ssl=bool(data.get(CONF_VERIFY_SSL, False)),
        )

        try:
            await client.async_connect()
            await client.async_disconnect()
        except AuthenticationError:
            return "invalid_auth"
        except ConnectionError:
            return "cannot_connect"
        except Exception:  # noqa: BLE001
            return "unknown"

        return None


async def async_create_fix_flow(
    _hass: HomeAssistant,
    issue_id: str,
    data: dict[str, Any] | None,
) -> RepairsFlow:
    """Create flow."""
    if issue_id.startswith("connection_failed_"):
        return ConnectionFailedRepairFlow(issue_id, data or {})

    # Default confirm flow for other issues
    return ConfirmRepairFlow()
