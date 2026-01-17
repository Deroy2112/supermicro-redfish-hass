"""Binary sensor platform for Supermicro Redfish integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiosupermicro.models.enums import Health, IntrusionSensor, PowerState
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from .const import (
    ENTITY_KEY_BMC_HEALTH,
    ENTITY_KEY_CHASSIS_HEALTH,
    ENTITY_KEY_CMOS_BATTERY,
    ENTITY_KEY_INTRUSION,
    ENTITY_KEY_LICENSE,
    ENTITY_KEY_LLDP_ENABLED,
    ENTITY_KEY_NTP_ENABLED,
    ENTITY_KEY_SYSTEM_HEALTH,
    ENTITY_KEY_SYSTEM_POWER,
)
from .entity import SupermicroRedfishEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SupermicroRedfishCoordinator
    from .data import CoordinatorData


@dataclass(frozen=True, kw_only=True)
class SupermicroBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Supermicro binary sensor entity."""

    value_fn: Callable[[CoordinatorData], bool | None]
    available_fn: Callable[[CoordinatorData], bool] = lambda _: True


BINARY_SENSOR_DESCRIPTIONS: tuple[SupermicroBinarySensorEntityDescription, ...] = (
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_SYSTEM_POWER,
        translation_key="system_power",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: data.system.power_state == PowerState.ON,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_SYSTEM_HEALTH,
        translation_key="system_health",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.system.status.health != Health.OK
        if data.system.status.health
        else None,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_CHASSIS_HEALTH,
        translation_key="chassis_health",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.chassis.status.health != Health.OK
        if data.chassis.status.health
        else None,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_BMC_HEALTH,
        translation_key="bmc_health",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.manager.status.health != Health.OK
        if data.manager.status.health
        else None,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_INTRUSION,
        translation_key="chassis_intrusion",
        device_class=BinarySensorDeviceClass.TAMPER,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.chassis.physical_security.intrusion_sensor
        != IntrusionSensor.NORMAL,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_LICENSE,
        translation_key="license_active",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.license.is_licensed,
        available_fn=lambda data: data.license.is_valid,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_CMOS_BATTERY,
        translation_key="cmos_battery",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: not data.power.battery.is_healthy
        if data.power.battery
        else None,
        available_fn=lambda data: data.power.battery is not None,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_NTP_ENABLED,
        translation_key="ntp_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.ntp.enabled,
        available_fn=lambda data: data.ntp.is_valid,
    ),
    SupermicroBinarySensorEntityDescription(
        key=ENTITY_KEY_LLDP_ENABLED,
        translation_key="lldp_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.lldp.enabled,
        available_fn=lambda data: data.lldp.is_valid,
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Supermicro Redfish binary sensors."""
    coordinator: SupermicroRedfishCoordinator = entry.runtime_data.coordinator

    entities: list[SupermicroRedfishBinarySensor] = []

    for description in BINARY_SENSOR_DESCRIPTIONS:
        # Check if this sensor is available
        if description.available_fn(coordinator.data):
            entities.append(
                SupermicroRedfishBinarySensor(coordinator, description)
            )

    async_add_entities(entities)


class SupermicroRedfishBinarySensor(SupermicroRedfishEntity, BinarySensorEntity):
    """Binary sensor for Supermicro Redfish."""

    entity_description: SupermicroBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        description: SupermicroBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.entity_description.available_fn(self.coordinator.data)
        )
