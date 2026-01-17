"""Base entity for Supermicro Redfish integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import SupermicroRedfishCoordinator
    from .data import CoordinatorData


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

        # Use system UUID as device identifier
        identifiers = {(DOMAIN, data.system.uuid)}

        # Add serial number as secondary identifier if available
        if data.system.serial_number:
            identifiers.add((DOMAIN, data.system.serial_number))

        return DeviceInfo(
            identifiers=identifiers,
            name=f"{data.system.manufacturer} {data.system.model}",
            manufacturer=data.system.manufacturer,
            model=data.system.model,
            serial_number=data.system.serial_number,
            sw_version=data.manager.firmware_version,
            hw_version=data.system.bios_version,
            configuration_url=f"https://{self.coordinator.config_entry.data['host']}",
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
