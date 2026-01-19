"""DataUpdateCoordinator for Supermicro Redfish integration."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import TYPE_CHECKING

from aiosupermicro.exceptions import AuthenticationError, ConnectionError
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BURST_DURATION,
    CONF_BURST_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_STATIC_INTERVAL,
    CONNECTION_ERROR_THRESHOLD,
    DEFAULT_BURST_DURATION,
    DEFAULT_BURST_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATIC_INTERVAL,
    DOMAIN,
)
from .data import CoordinatorData

if TYPE_CHECKING:
    from aiosupermicro import SupermicroRedfishClient
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class SupermicroRedfishCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinator for Supermicro Redfish data updates."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: SupermicroRedfishClient,
    ) -> None:
        """Initialize the coordinator."""
        self._client = client
        self._connection_errors = 0
        self._last_static_update: float = 0
        self._static_data_cache: CoordinatorData | None = None

        # Get intervals from options
        self._scan_interval = int(
            entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        self._burst_interval = int(
            entry.options.get(CONF_BURST_INTERVAL, DEFAULT_BURST_INTERVAL)
        )
        self._burst_duration = int(
            entry.options.get(CONF_BURST_DURATION, DEFAULT_BURST_DURATION)
        )
        self._static_interval = int(
            entry.options.get(CONF_STATIC_INTERVAL, DEFAULT_STATIC_INTERVAL)
        )

        # Burst mode task
        self._burst_task: asyncio.Task[None] | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._scan_interval),
        )

    @property
    def client(self) -> SupermicroRedfishClient:
        """Return the API client."""
        return self._client

    def enable_burst_mode(self) -> None:
        """Enable burst mode for faster polling after user actions."""
        # Cancel existing burst task if any
        if self._burst_task and not self._burst_task.done():
            self._burst_task.cancel()

        self._burst_task = self.hass.async_create_task(
            self._async_burst_polling(),
            name="supermicro_burst_polling",
        )
        _LOGGER.debug("Burst mode enabled for %s seconds", self._burst_duration)

    async def _async_burst_polling(self) -> None:
        """Run burst polling for a limited duration."""
        end_time = time.time() + self._burst_duration
        while time.time() < end_time:
            await asyncio.sleep(self._burst_interval)
            await self.async_request_refresh()
        _LOGGER.debug("Burst mode ended")

    def _should_update_static_data(self) -> bool:
        """Check if static data should be updated."""
        return time.time() - self._last_static_update > self._static_interval

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from the API."""
        try:
            # Always fetch dynamic data
            dynamic = await self._client.async_get_dynamic_data()

            # Fetch static data if needed (includes OEM endpoints)
            if self._should_update_static_data() or self._static_data_cache is None:
                static = await self._client.async_get_static_data()
                self._last_static_update = time.time()

                data = CoordinatorData(
                    system=static.system,
                    chassis=static.chassis,
                    manager=static.manager,
                    thermal=dynamic.thermal,
                    power=dynamic.power,
                    fan_mode=dynamic.fan_mode,
                    ntp=static.ntp,
                    lldp=static.lldp,
                    snooping=dynamic.snooping,
                    license=static.license,
                    network_protocol=static.network_protocol,
                )
                self._static_data_cache = data
            else:
                # Use cached static data with fresh dynamic data
                data = CoordinatorData(
                    system=self._static_data_cache.system,
                    chassis=self._static_data_cache.chassis,
                    manager=self._static_data_cache.manager,
                    thermal=dynamic.thermal,
                    power=dynamic.power,
                    fan_mode=dynamic.fan_mode,
                    ntp=self._static_data_cache.ntp,
                    lldp=self._static_data_cache.lldp,
                    snooping=dynamic.snooping,
                    license=self._static_data_cache.license,
                    network_protocol=self._static_data_cache.network_protocol,
                )

            # Reset connection error counter on success
            self._connection_errors = 0

            return data

        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err

        except ConnectionError as err:
            self._connection_errors += 1
            _LOGGER.warning(
                "Connection error (%d/%d): %s",
                self._connection_errors,
                CONNECTION_ERROR_THRESHOLD,
                err,
            )

            # Create repair issue after threshold
            if self._connection_errors >= CONNECTION_ERROR_THRESHOLD:
                await self._async_create_repair_issue()

            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="connection_failed",
                translation_placeholders={"host": self._client._host},
            ) from err

        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _async_create_repair_issue(self) -> None:
        """Create a repair issue for connection failures."""
        from homeassistant.helpers import issue_registry as ir

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"connection_failed_{self.config_entry.entry_id}",
            is_fixable=True,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="connection_failed",
            translation_placeholders={
                "host": str(self.config_entry.data.get("host", "unknown")),
                "error_count": str(self._connection_errors),
            },
            data={"entry_id": self.config_entry.entry_id},
        )

    async def async_refresh_static_data(self) -> None:
        """Force refresh of static data."""
        self._last_static_update = 0
        await self.async_request_refresh()
