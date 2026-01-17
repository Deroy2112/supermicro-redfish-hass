"""Sensor platform for Supermicro Redfish integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)

from .const import (
    ENTITY_KEY_API_RESPONSE_TIME,
    ENTITY_KEY_BIOS_VERSION,
    ENTITY_KEY_BMC_FIRMWARE,
    ENTITY_KEY_POST_CODE,
    ENTITY_KEY_POWER_CONSUMPTION,
)
from .entity import SupermicroRedfishEntity, SupermicroRedfishSensorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SupermicroRedfishCoordinator
    from .data import CoordinatorData


@dataclass(frozen=True, kw_only=True)
class SupermicroSensorEntityDescription(SensorEntityDescription):
    """Describes a Supermicro sensor entity."""

    value_fn: Callable[[CoordinatorData], Any]
    available_fn: Callable[[CoordinatorData], bool] = lambda _: True


SENSOR_DESCRIPTIONS: tuple[SupermicroSensorEntityDescription, ...] = (
    # Essential sensors - enabled by default
    SupermicroSensorEntityDescription(
        key=ENTITY_KEY_POWER_CONSUMPTION,
        translation_key="power_consumption",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data.power.total_power_consumed_watts,
        available_fn=lambda data: data.power.total_power_consumed_watts is not None,
    ),
    # Diagnostic sensors - disabled by default
    SupermicroSensorEntityDescription(
        key=ENTITY_KEY_BIOS_VERSION,
        translation_key="bios_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.system.bios_version,
    ),
    SupermicroSensorEntityDescription(
        key=ENTITY_KEY_BMC_FIRMWARE,
        translation_key="bmc_firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.manager.firmware_version,
    ),
    SupermicroSensorEntityDescription(
        key=ENTITY_KEY_POST_CODE,
        translation_key="post_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.snooping.post_code,
        available_fn=lambda data: data.snooping.is_valid,
    ),
    SupermicroSensorEntityDescription(
        key=ENTITY_KEY_API_RESPONSE_TIME,
        translation_key="api_response_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda _data: None,  # Handled separately
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Supermicro Redfish sensors."""
    coordinator: SupermicroRedfishCoordinator = entry.runtime_data.coordinator
    data: CoordinatorData = coordinator.data

    entities: list[SensorEntity] = []

    # Add static sensors
    for description in SENSOR_DESCRIPTIONS:
        if description.key == ENTITY_KEY_API_RESPONSE_TIME:
            entities.append(ApiResponseTimeSensor(coordinator, description))
        elif description.available_fn(data):
            entities.append(SupermicroRedfishSensor(coordinator, description))

    # Add dynamic temperature sensors
    for temp in data.thermal.available_temperatures:
        entities.append(
            TemperatureSensor(
                coordinator,
                temp.member_id,
                temp.name,
            )
        )

    # Add dynamic fan sensors
    for fan in data.thermal.available_fans:
        entities.append(
            FanSensor(
                coordinator,
                fan.member_id,
                fan.name,
            )
        )

    # Add dynamic voltage sensors
    for voltage in data.power.available_voltages:
        entities.append(
            VoltageSensor(
                coordinator,
                voltage.member_id,
                voltage.name,
            )
        )

    async_add_entities(entities)


class SupermicroRedfishSensor(SupermicroRedfishEntity, SensorEntity):
    """Sensor for Supermicro Redfish."""

    entity_description: SupermicroSensorEntityDescription

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        description: SupermicroSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.entity_description.available_fn(self.coordinator.data)
        )


class ApiResponseTimeSensor(SupermicroRedfishEntity, SensorEntity):
    """Sensor for API response time."""

    entity_description: SupermicroSensorEntityDescription

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        description: SupermicroSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float:
        """Return the average API response time."""
        return float(round(self.coordinator.client.stats.avg_response_time_ms, 1))


class TemperatureSensor(SupermicroRedfishSensorEntity, SensorEntity):
    """Temperature sensor for Supermicro Redfish."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        member_id: str,
        sensor_name: str,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, "temperature", member_id, sensor_name)

    @property
    def native_value(self) -> float | None:
        """Return the temperature reading."""
        temp = self.coordinator.data.thermal.get_temperature(self._member_id)
        return temp.reading_celsius if temp else None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        temp = self.coordinator.data.thermal.get_temperature(self._member_id)
        return temp is not None and temp.is_available


class FanSensor(SupermicroRedfishSensorEntity, SensorEntity):
    """Fan speed sensor for Supermicro Redfish."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "RPM"
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        member_id: str,
        sensor_name: str,
    ) -> None:
        """Initialize the fan sensor."""
        super().__init__(coordinator, "fan", member_id, sensor_name)

    @property
    def native_value(self) -> int | None:
        """Return the fan speed reading."""
        fan = self.coordinator.data.thermal.get_fan(self._member_id)
        return fan.reading_rpm if fan else None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        fan = self.coordinator.data.thermal.get_fan(self._member_id)
        return fan is not None and fan.is_available


class VoltageSensor(SupermicroRedfishSensorEntity, SensorEntity):
    """Voltage sensor for Supermicro Redfish."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: SupermicroRedfishCoordinator,
        member_id: str,
        sensor_name: str,
    ) -> None:
        """Initialize the voltage sensor."""
        super().__init__(coordinator, "voltage", member_id, sensor_name)

    @property
    def native_value(self) -> float | None:
        """Return the voltage reading."""
        voltage = self.coordinator.data.power.get_voltage(self._member_id)
        return voltage.reading_volts if voltage else None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        voltage = self.coordinator.data.power.get_voltage(self._member_id)
        return voltage is not None and voltage.is_available
