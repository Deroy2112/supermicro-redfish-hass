"""The Supermicro Redfish integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeAlias

from aiosupermicro import SupermicroRedfishClient
from aiosupermicro.exceptions import AuthenticationError, ConnectionError
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_MAX_CONCURRENT_REQUESTS,
    CONF_VERIFY_SSL,
    DEFAULT_CONCURRENT_REQUESTS,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SupermicroRedfishCoordinator
from .data import SupermicroRedfishRuntimeData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

SupermicroRedfishConfigEntry: TypeAlias = "ConfigEntry[SupermicroRedfishRuntimeData]"


async def async_setup_entry(
    hass: HomeAssistant, entry: SupermicroRedfishConfigEntry
) -> bool:
    """Set up Supermicro Redfish from a config entry."""
    session = async_get_clientsession(hass, verify_ssl=entry.data.get(CONF_VERIFY_SSL, False))

    client = SupermicroRedfishClient(
        session=session,
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
    )

    # Configure request throttling
    max_requests = entry.options.get(
        CONF_MAX_CONCURRENT_REQUESTS, DEFAULT_CONCURRENT_REQUESTS
    )
    client.set_max_concurrent_requests(max_requests)

    # Test connection and authenticate
    try:
        await client.async_connect()
    except AuthenticationError as err:
        await client.async_disconnect()
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_failed",
        ) from err
    except ConnectionError as err:
        await client.async_disconnect()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="connection_failed",
            translation_placeholders={"host": entry.data[CONF_HOST]},
        ) from err

    # Create coordinator
    coordinator = SupermicroRedfishCoordinator(hass, entry, client)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store runtime data
    entry.runtime_data = SupermicroRedfishRuntimeData(
        client=client,
        coordinator=coordinator,
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SupermicroRedfishConfigEntry
) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Disconnect client
        await entry.runtime_data.client.async_disconnect()

    return unload_ok


async def async_update_options(
    hass: HomeAssistant, entry: SupermicroRedfishConfigEntry
) -> None:
    """Handle options update."""
    # Reload integration to apply new options
    await hass.config_entries.async_reload(entry.entry_id)
