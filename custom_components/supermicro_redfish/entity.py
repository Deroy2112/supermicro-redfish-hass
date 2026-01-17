"""Base entity for Supermicro Redfish integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER

if TYPE_CHECKING:
    from .coordinator import SupermicroRedfishCoordinator
    from .data import CoordinatorData


def _get_device_name(data: CoordinatorData, host: str) -> str:
    """Get best available device name using fallback chain.

    Priority:
    1. Chassis serial number (if set by user in BIOS)
    2. OEM Board serial number (hardware-fixed, always available)
    3. Host as last fallback
    """
    if data.chassis.serial_number:
        return f"{MANUFACTURER} {data.chassis.serial_number}"
    if data.chassis.oem.board_serial_number:
        return f"{MANUFACTURER} {data.chassis.oem.board_serial_number}"
    return f"{MANUFACTURER} Server ({host})"


def _get_serial_number(data: CoordinatorData) -> str | None:
    """Get best available serial number for device registry."""
    return data.chassis.serial_number or data.chassis.oem.board_serial_number


class SupermicroRedfishEntity(CoordinatorEntity["SupermicroRedfishCoordinator"]):
    """Base entity for Supermicro Redfish."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entity_key = entity_key

        # Build unique ID from entry ID and entity key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        data: CoordinatorData = self.coordinator.data
        host: str = self.coordinator.config_entry.data["host"]

        return DeviceInfo(
            identifiers={(DOMAIN, data.system.uuid)},
            name=_get_device_name(data, host),
            manufacturer=data.chassis.manufacturer or MANUFACTURER,
            model=data.chassis.model,
            serial_number=_get_serial_number(data),
            sw_version=data.manager.firmware_version,
            hw_version=data.chassis.model,
            configuration_url=f"https://{host}",
        )

    def _enable_burst_mode(self) -> None:
        """Enable burst mode after user action."""
        self.coordinator.enable_burst_mode()


class SupermicroRedfishSensorEntity(SupermicroRedfishEntity):
    """Base entity for dynamic sensors (temperature, fan, voltage)."""

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        entity_key: str,
        member_id: str,
        sensor_name: str,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator, f"{entity_key}_{member_id}")
        self._member_id = member_id
        self._sensor_name = sensor_name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._sensor_name
