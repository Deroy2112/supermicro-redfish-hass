"""Tests for Supermicro Redfish integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.supermicro_redfish.const import DOMAIN


async def test_setup_entry_auth_failed(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry_data: dict,
) -> None:
    """Test setup entry with authentication failure."""
    from aiosupermicro.exceptions import AuthenticationError

    mock_client.async_connect = AsyncMock(side_effect=AuthenticationError("Invalid credentials"))

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test",
        data=mock_config_entry_data,
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.supermicro_redfish.SupermicroRedfishClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.supermicro_redfish.async_get_clientsession",
            return_value=MagicMock(),
        ),
        pytest.raises(ConfigEntryAuthFailed),
    ):
        from custom_components.supermicro_redfish import async_setup_entry

        await async_setup_entry(hass, entry)


async def test_setup_entry_connection_failed(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry_data: dict,
) -> None:
    """Test setup entry with connection failure."""
    from aiosupermicro.exceptions import ConnectionError

    mock_client.async_connect = AsyncMock(side_effect=ConnectionError("Connection refused"))

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test",
        data=mock_config_entry_data,
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.supermicro_redfish.SupermicroRedfishClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.supermicro_redfish.async_get_clientsession",
            return_value=MagicMock(),
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        from custom_components.supermicro_redfish import async_setup_entry

        await async_setup_entry(hass, entry)
