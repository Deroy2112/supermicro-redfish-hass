"""Switch platform for Supermicro Redfish integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aiosupermicro.models.enums import IndicatorLED
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory

from .const import (
    ENTITY_KEY_HTTP_PROTOCOL,
    ENTITY_KEY_INDICATOR_LED,
    ENTITY_KEY_IPMI_PROTOCOL,
    ENTITY_KEY_SNMP_PROTOCOL,
    ENTITY_KEY_SSH_PROTOCOL,
)
from .entity import SupermicroRedfishEntity

if TYPE_CHECKING:
    from aiosupermicro import SupermicroRedfishClient
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SupermicroRedfishCoordinator
    from .data import CoordinatorData


@dataclass(frozen=True, kw_only=True)
class SupermicroSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Supermicro switch entity."""

    value_fn: Callable[[CoordinatorData], bool | None]
    turn_on_fn: Callable[[SupermicroRedfishClient], Coroutine[Any, Any, None]]
    turn_off_fn: Callable[[SupermicroRedfishClient], Coroutine[Any, Any, None]]
    available_fn: Callable[[CoordinatorData], bool] = lambda _: True


SWITCH_DESCRIPTIONS: tuple[SupermicroSwitchEntityDescription, ...] = (
    # Essential switches - enabled by default
    SupermicroSwitchEntityDescription(
        key=ENTITY_KEY_INDICATOR_LED,
        translation_key="indicator_led",
        value_fn=lambda data: data.system.indicator_led == IndicatorLED.LIT
        or data.system.indicator_led == IndicatorLED.BLINKING,
        turn_on_fn=lambda client: client.async_set_indicator_led(IndicatorLED.LIT),
        turn_off_fn=lambda client: client.async_set_indicator_led(IndicatorLED.OFF),
    ),
    # Protocol switches - disabled by default
    SupermicroSwitchEntityDescription(
        key=ENTITY_KEY_HTTP_PROTOCOL,
        translation_key="http_protocol",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.network_protocol.http.protocol_enabled,
        turn_on_fn=lambda client: client.async_set_protocol_enabled("HTTP", True),
        turn_off_fn=lambda client: client.async_set_protocol_enabled("HTTP", False),
        available_fn=lambda data: data.network_protocol.is_valid,
    ),
    SupermicroSwitchEntityDescription(
        key=ENTITY_KEY_SSH_PROTOCOL,
        translation_key="ssh_protocol",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.network_protocol.ssh.protocol_enabled,
        turn_on_fn=lambda client: client.async_set_protocol_enabled("SSH", True),
        turn_off_fn=lambda client: client.async_set_protocol_enabled("SSH", False),
        available_fn=lambda data: data.network_protocol.is_valid,
    ),
    SupermicroSwitchEntityDescription(
        key=ENTITY_KEY_IPMI_PROTOCOL,
        translation_key="ipmi_protocol",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.network_protocol.ipmi.protocol_enabled,
        turn_on_fn=lambda client: client.async_set_protocol_enabled("IPMI", True),
        turn_off_fn=lambda client: client.async_set_protocol_enabled("IPMI", False),
        available_fn=lambda data: data.network_protocol.is_valid,
    ),
    SupermicroSwitchEntityDescription(
        key=ENTITY_KEY_SNMP_PROTOCOL,
        translation_key="snmp_protocol",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.network_protocol.snmp.protocol_enabled,
        turn_on_fn=lambda client: client.async_set_protocol_enabled("SNMP", True),
        turn_off_fn=lambda client: client.async_set_protocol_enabled("SNMP", False),
        available_fn=lambda data: data.network_protocol.is_valid,
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Supermicro Redfish switches."""
    coordinator: SupermicroRedfishCoordinator = entry.runtime_data.coordinator

    entities: list[SupermicroRedfishSwitch] = []

    for description in SWITCH_DESCRIPTIONS:
        if description.available_fn(coordinator.data):
            entities.append(SupermicroRedfishSwitch(coordinator, description))

    async_add_entities(entities)


class SupermicroRedfishSwitch(SupermicroRedfishEntity, SwitchEntity):
    """Switch for Supermicro Redfish."""

    entity_description: SupermicroSwitchEntityDescription

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        description: SupermicroSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.entity_description.available_fn(self.coordinator.data)
        )

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self.coordinator.client)
        self._enable_burst_mode()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self.coordinator.client)
        self._enable_burst_mode()
        await self.coordinator.async_request_refresh()
