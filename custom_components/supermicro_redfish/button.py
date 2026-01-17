"""Button platform for Supermicro Redfish integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aiosupermicro.models.enums import ResetType
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory

from .const import (
    ENTITY_KEY_BMC_RESTART,
    ENTITY_KEY_FORCE_RESTART,
    ENTITY_KEY_GRACEFUL_RESTART,
    ENTITY_KEY_GRACEFUL_SHUTDOWN,
    ENTITY_KEY_POWER_OFF,
    ENTITY_KEY_POWER_ON,
    ENTITY_KEY_RESET_INTRUSION,
    ENTITY_KEY_SEND_NMI,
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
class SupermicroButtonEntityDescription(ButtonEntityDescription):
    """Describes a Supermicro button entity."""

    press_fn: Callable[[SupermicroRedfishClient], Coroutine[Any, Any, None]]
    available_fn: Callable[[CoordinatorData], bool] = lambda _: True


BUTTON_DESCRIPTIONS: tuple[SupermicroButtonEntityDescription, ...] = (
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_POWER_ON,
        translation_key="power_on",
        icon="mdi:power",
        press_fn=lambda client: client.async_system_reset(ResetType.ON),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_POWER_OFF,
        translation_key="power_off",
        icon="mdi:power-off",
        press_fn=lambda client: client.async_system_reset(ResetType.FORCE_OFF),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_GRACEFUL_SHUTDOWN,
        translation_key="graceful_shutdown",
        icon="mdi:power-sleep",
        press_fn=lambda client: client.async_system_reset(ResetType.GRACEFUL_SHUTDOWN),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_GRACEFUL_RESTART,
        translation_key="graceful_restart",
        device_class=ButtonDeviceClass.RESTART,
        press_fn=lambda client: client.async_system_reset(ResetType.GRACEFUL_RESTART),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_FORCE_RESTART,
        translation_key="force_restart",
        device_class=ButtonDeviceClass.RESTART,
        press_fn=lambda client: client.async_system_reset(ResetType.FORCE_RESTART),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_BMC_RESTART,
        translation_key="bmc_restart",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda client: client.async_manager_reset(ResetType.GRACEFUL_RESTART),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_SEND_NMI,
        translation_key="send_nmi",
        icon="mdi:alert-octagon",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda client: client.async_system_reset(ResetType.NMI),
    ),
    SupermicroButtonEntityDescription(
        key=ENTITY_KEY_RESET_INTRUSION,
        translation_key="reset_intrusion",
        icon="mdi:shield-refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        press_fn=lambda client: client.async_reset_intrusion_sensor(),
        available_fn=lambda data: data.chassis.is_intruded,
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Supermicro Redfish buttons."""
    coordinator: SupermicroRedfishCoordinator = entry.runtime_data.coordinator

    entities: list[SupermicroRedfishButton] = []

    for description in BUTTON_DESCRIPTIONS:
        # Always add buttons (availability is checked dynamically)
        entities.append(SupermicroRedfishButton(coordinator, description))

    async_add_entities(entities)


class SupermicroRedfishButton(SupermicroRedfishEntity, ButtonEntity):
    """Button for Supermicro Redfish."""

    entity_description: SupermicroButtonEntityDescription

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        description: SupermicroButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.entity_description.available_fn(self.coordinator.data)
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(self.coordinator.client)
        self._enable_burst_mode()
        await self.coordinator.async_request_refresh()
