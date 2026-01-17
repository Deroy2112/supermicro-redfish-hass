"""Tests for Supermicro Redfish config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.supermicro_redfish.const import CONF_VERIFY_SSL, DOMAIN


@pytest.fixture
def mock_client_class() -> MagicMock:
    """Return mock SupermicroRedfishClient class."""
    mock_system = MagicMock()
    mock_system.manufacturer = "Supermicro"
    mock_system.model = "X12DPi-N6"

    mock_client = MagicMock()
    mock_client.async_connect = AsyncMock()
    mock_client.async_disconnect = AsyncMock()
    mock_client.async_get_system = AsyncMock(return_value=mock_system)

    return mock_client


async def test_form_user(
    hass: HomeAssistant,
    mock_client_class: MagicMock,
) -> None:
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with (
        patch(
            "custom_components.supermicro_redfish.config_flow.SupermicroRedfishClient",
            return_value=mock_client_class,
        ),
        patch(
            "custom_components.supermicro_redfish.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "ADMIN",
                CONF_PASSWORD: "password",
                CONF_VERIFY_SSL: False,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Supermicro X12DPi-N6"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "ADMIN",
        CONF_PASSWORD: "password",
        CONF_VERIFY_SSL: False,
    }


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test handling invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    from aiosupermicro.exceptions import AuthenticationError

    mock_client = MagicMock()
    mock_client.async_connect = AsyncMock(side_effect=AuthenticationError("Invalid credentials"))
    mock_client.async_disconnect = AsyncMock()

    with patch(
        "custom_components.supermicro_redfish.config_flow.SupermicroRedfishClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "ADMIN",
                CONF_PASSWORD: "wrong",
                CONF_VERIFY_SSL: False,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test handling connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    from aiosupermicro.exceptions import ConnectionError

    mock_client = MagicMock()
    mock_client.async_connect = AsyncMock(side_effect=ConnectionError("Connection refused"))
    mock_client.async_disconnect = AsyncMock()

    with patch(
        "custom_components.supermicro_redfish.config_flow.SupermicroRedfishClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "ADMIN",
                CONF_PASSWORD: "password",
                CONF_VERIFY_SSL: False,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
