"""Config flow for Supermicro Redfish integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiosupermicro import SupermicroRedfishClient
from aiosupermicro.exceptions import AuthenticationError, ConnectionError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BURST_DURATION,
    CONF_BURST_INTERVAL,
    CONF_MAX_CONCURRENT_REQUESTS,
    CONF_SCAN_INTERVAL,
    CONF_STATIC_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_BURST_DURATION,
    DEFAULT_BURST_INTERVAL,
    DEFAULT_CONCURRENT_REQUESTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATIC_INTERVAL,
    DOMAIN,
    MAX_BURST_DURATION,
    MAX_BURST_INTERVAL,
    MAX_CONCURRENT_REQUESTS,
    MAX_SCAN_INTERVAL,
    MAX_STATIC_INTERVAL,
    MIN_BURST_DURATION,
    MIN_BURST_INTERVAL,
    MIN_CONCURRENT_REQUESTS,
    MIN_SCAN_INTERVAL,
    MIN_STATIC_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)


class SupermicroRedfishConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Supermicro Redfish."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._reauth_entry: ConfigEntry | None = None
        self._reconfigure_entry: ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check for duplicate entries
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            # Test connection
            error = await self._async_test_connection(user_input)
            if error:
                errors["base"] = error
            else:
                # Get system info for title
                title = await self._async_get_title(user_input)
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, _entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth flow."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None and self._reauth_entry:
            # Merge with existing data
            new_data = {**self._reauth_entry.data, **user_input}

            # Test connection
            error = await self._async_test_connection(new_data)
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data=new_data,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "host": self._reauth_entry.data[CONF_HOST] if self._reauth_entry else "",
            },
        )

    async def async_step_reconfigure(
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfigure flow."""
        self._reconfigure_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reconfigure_confirm()

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfigure confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None and self._reconfigure_entry:
            # Check for duplicate host if changed
            if user_input[CONF_HOST] != self._reconfigure_entry.data[CONF_HOST]:
                self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            # Test connection
            error = await self._async_test_connection(user_input)
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    self._reconfigure_entry,
                    data=user_input,
                )

        # Pre-fill with existing data
        existing_data = self._reconfigure_entry.data if self._reconfigure_entry else {}

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=existing_data.get(CONF_HOST, "")): str,
                    vol.Required(CONF_USERNAME, default=existing_data.get(CONF_USERNAME, "")): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_VERIFY_SSL, default=existing_data.get(CONF_VERIFY_SSL, False)): bool,
                }
            ),
            errors=errors,
        )

    async def _async_test_connection(self, data: dict[str, Any]) -> str | None:
        """Test connection to the BMC and return error key if failed."""
        session = async_get_clientsession(
            self.hass, verify_ssl=data.get(CONF_VERIFY_SSL, False)
        )

        client = SupermicroRedfishClient(
            session=session,
            host=data[CONF_HOST],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            verify_ssl=data.get(CONF_VERIFY_SSL, False),
        )

        try:
            await client.async_connect()
            await client.async_disconnect()
        except AuthenticationError:
            return "invalid_auth"
        except ConnectionError:
            return "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during connection test")
            return "unknown"

        return None

    async def _async_get_title(self, data: dict[str, Any]) -> str:
        """Get title for the config entry."""
        session = async_get_clientsession(
            self.hass, verify_ssl=data.get(CONF_VERIFY_SSL, False)
        )

        client = SupermicroRedfishClient(
            session=session,
            host=data[CONF_HOST],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            verify_ssl=data.get(CONF_VERIFY_SSL, False),
        )

        try:
            await client.async_connect()
            system = await client.async_get_system()
            await client.async_disconnect()
            if system.model and system.model != "Unknown":
                return f"{system.manufacturer} {system.model}"
        except Exception:  # noqa: BLE001
            pass

        return f"Supermicro BMC ({data[CONF_HOST]})"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return SupermicroRedfishOptionsFlow(config_entry)


class SupermicroRedfishOptionsFlow(OptionsFlow):
    """Handle options flow for Supermicro Redfish."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_BURST_INTERVAL,
                        default=options.get(CONF_BURST_INTERVAL, DEFAULT_BURST_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_BURST_INTERVAL, max=MAX_BURST_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_BURST_DURATION,
                        default=options.get(CONF_BURST_DURATION, DEFAULT_BURST_DURATION),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_BURST_DURATION, max=MAX_BURST_DURATION),
                    ),
                    vol.Optional(
                        CONF_STATIC_INTERVAL,
                        default=options.get(CONF_STATIC_INTERVAL, DEFAULT_STATIC_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_STATIC_INTERVAL, max=MAX_STATIC_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_MAX_CONCURRENT_REQUESTS,
                        default=options.get(CONF_MAX_CONCURRENT_REQUESTS, DEFAULT_CONCURRENT_REQUESTS),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_CONCURRENT_REQUESTS, max=MAX_CONCURRENT_REQUESTS),
                    ),
                }
            ),
        )
