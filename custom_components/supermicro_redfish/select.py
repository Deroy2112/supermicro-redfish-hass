"""Select platform for Supermicro Redfish integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiosupermicro.models.enums import BootSource, BootSourceEnabled, FanModeType
from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory

from .const import ENTITY_KEY_BOOT_SOURCE, ENTITY_KEY_FAN_MODE
from .entity import SupermicroRedfishEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SupermicroRedfishCoordinator


# Map FanModeType values to display names
FAN_MODE_NAMES: dict[str, str] = {
    FanModeType.STANDARD: "Standard",
    FanModeType.FULL_SPEED: "Full Speed",
    FanModeType.OPTIMAL: "Optimal",
    FanModeType.HEAVY_IO: "Heavy I/O",
    FanModeType.PUE_OPTIMAL: "PUE Optimal",
}

# Map BootSource values to display names
BOOT_SOURCE_NAMES: dict[str, str] = {
    BootSource.NONE: "None",
    BootSource.PXE: "PXE",
    BootSource.HDD: "HDD",
    BootSource.CD: "CD/DVD",
    BootSource.USB: "USB",
    BootSource.BIOS_SETUP: "BIOS Setup",
    BootSource.UEFI_TARGET: "UEFI Target",
    BootSource.FLOPPY: "Floppy",
    BootSource.SD_CARD: "SD Card",
    BootSource.UEFI_HTTP: "UEFI HTTP",
    BootSource.REMOTE_DRIVE: "Remote Drive",
    BootSource.DIAGS: "Diagnostics",
    BootSource.UTILITIES: "Utilities",
}


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Supermicro Redfish select entities."""
    coordinator: SupermicroRedfishCoordinator = entry.runtime_data.coordinator

    entities: list[SelectEntity] = []

    # Add fan mode select if available
    if coordinator.data.fan_mode.is_valid:
        entities.append(FanModeSelect(coordinator))

    # Add boot source select if boot options are available
    if coordinator.data.system.boot.boot_source_options:
        entities.append(BootSourceSelect(coordinator))

    async_add_entities(entities)


class FanModeSelect(SupermicroRedfishEntity, SelectEntity):
    """Select entity for fan mode."""

    _attr_translation_key = "fan_mode"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: SupermicroRedfishCoordinator) -> None:
        """Initialize the fan mode select."""
        super().__init__(coordinator, ENTITY_KEY_FAN_MODE)

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        available_modes = self.coordinator.data.fan_mode.available_modes
        return [
            FAN_MODE_NAMES.get(str(mode), str(mode))
            for mode in available_modes
        ]

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        current_mode = self.coordinator.data.fan_mode.mode
        return FAN_MODE_NAMES.get(str(current_mode), str(current_mode))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Reverse lookup: display name -> FanModeType value
        mode_value = None
        for mode_type, name in FAN_MODE_NAMES.items():
            if name == option:
                mode_value = mode_type
                break

        if mode_value is None:
            # Fallback: use option as-is if not found in mapping
            mode_value = option

        await self.coordinator.client.async_set_fan_mode(mode_value)
        self._enable_burst_mode()
        await self.coordinator.async_request_refresh()


class BootSourceSelect(SupermicroRedfishEntity, SelectEntity):
    """Select entity for boot source override."""

    _attr_translation_key = "boot_source"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:boot"

    def __init__(self, coordinator: SupermicroRedfishCoordinator) -> None:
        """Initialize the boot source select."""
        super().__init__(coordinator, ENTITY_KEY_BOOT_SOURCE)

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        boot_options = self.coordinator.data.system.boot.boot_source_options
        return [
            BOOT_SOURCE_NAMES.get(opt, opt)
            for opt in boot_options
        ]

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        current_target = self.coordinator.data.system.boot.boot_source_override_target
        if current_target is None:
            return None
        return BOOT_SOURCE_NAMES.get(str(current_target), str(current_target))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        boot = self.coordinator.data.system.boot
        return {
            "boot_override_enabled": str(boot.boot_source_override_enabled),
        }

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Reverse lookup: display name -> BootSource value
        target_value = None
        for boot_source, name in BOOT_SOURCE_NAMES.items():
            if name == option:
                target_value = boot_source
                break

        if target_value is None:
            target_value = option

        # Set boot source with "Once" enabled
        await self.coordinator.client.async_set_boot_source(
            target=target_value,
            enabled=BootSourceEnabled.ONCE,
        )
        self._enable_burst_mode()
        await self.coordinator.async_request_refresh()
