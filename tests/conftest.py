"""Fixtures for Supermicro Redfish tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from custom_components.supermicro_redfish.const import CONF_VERIFY_SSL, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,  # noqa: ARG001
) -> None:
    """Enable custom integrations for all tests."""


@pytest.fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Return mock config entry data."""
    return {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "ADMIN",
        CONF_PASSWORD: "password",
        CONF_VERIFY_SSL: False,
    }


@pytest.fixture
def mock_system() -> MagicMock:
    """Return mock System object."""
    system = MagicMock()
    system.id = "1"
    system.name = "System"
    system.uuid = "12345678-1234-1234-1234-123456789012"
    system.manufacturer = "Supermicro"
    system.model = "X12DPi-N6"
    system.serial_number = "S123456789"
    system.power_state = MagicMock()
    system.power_state.value = "On"
    system.bios_version = "2.1"
    system.indicator_led = MagicMock()
    system.indicator_led.value = "Off"
    system.processor_count = 2
    system.total_memory_gib = 256
    system.status = MagicMock()
    system.status.health = MagicMock()
    system.status.health.value = "OK"
    system.status.state = MagicMock()
    system.status.state.value = "Enabled"
    system.boot = MagicMock()
    system.boot.boot_source_override_target = None
    system.boot.boot_source_override_enabled = MagicMock()
    system.boot.boot_source_options = ["Pxe", "Hdd", "Cd", "Usb", "BiosSetup"]
    system.is_valid = True
    return system


@pytest.fixture
def mock_client(mock_system: MagicMock) -> MagicMock:
    """Return mock SupermicroRedfishClient."""
    client = MagicMock()
    client._host = "192.168.1.100"

    # Connection methods
    client.async_connect = AsyncMock()
    client.async_disconnect = AsyncMock()
    client.async_test_connection = AsyncMock()
    client.async_get_system = AsyncMock(return_value=mock_system)

    # Config
    client.set_max_concurrent_requests = MagicMock()

    # Stats
    client.stats = MagicMock()
    client.stats.total_requests = 100
    client.stats.cache_hits = 50
    client.stats.errors = 0
    client.stats.avg_response_time_ms = 150.0
    client.stats.cache_hit_rate = 50.0

    return client
