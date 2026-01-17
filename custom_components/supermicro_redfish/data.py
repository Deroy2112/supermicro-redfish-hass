"""Runtime data for the Supermicro Redfish integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiosupermicro import SupermicroRedfishClient
    from aiosupermicro.models import (
        Chassis,
        FanMode,
        License,
        Manager,
        NetworkProtocol,
        Power,
        Snooping,
        System,
        Thermal,
    )
    from aiosupermicro.models.oem import LLDP, NTP

    from .coordinator import SupermicroRedfishCoordinator


@dataclass
class CoordinatorData:
    """Data class for coordinator data."""

    system: System
    chassis: Chassis
    manager: Manager
    thermal: Thermal
    power: Power
    fan_mode: FanMode
    ntp: NTP
    lldp: LLDP
    snooping: Snooping
    license: License
    network_protocol: NetworkProtocol


@dataclass
class SupermicroRedfishRuntimeData:
    """Runtime data for Supermicro Redfish integration."""

    client: SupermicroRedfishClient
    coordinator: SupermicroRedfishCoordinator
