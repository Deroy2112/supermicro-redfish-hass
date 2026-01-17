"""Diagnostics support for Supermicro Redfish integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .data import SupermicroRedfishRuntimeData

# Keys to redact from diagnostic data
TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "serial_number",
    "uuid",
    "token",
    "session_uri",
    "mac_address",
    "board_serial_number",
}


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data: SupermicroRedfishRuntimeData = entry.runtime_data
    coordinator = runtime_data.coordinator
    client = runtime_data.client

    # Build coordinator data dict
    data = coordinator.data
    coordinator_data: dict[str, Any] = {}

    # System
    coordinator_data["system"] = {
        "id": data.system.id,
        "name": data.system.name,
        "manufacturer": data.system.manufacturer,
        "model": data.system.model,
        "power_state": str(data.system.power_state),
        "bios_version": data.system.bios_version,
        "indicator_led": str(data.system.indicator_led),
        "processor_count": data.system.processor_count,
        "total_memory_gib": data.system.total_memory_gib,
        "status_health": str(data.system.status.health) if data.system.status.health else None,
        "status_state": str(data.system.status.state) if data.system.status.state else None,
    }

    # Chassis
    coordinator_data["chassis"] = {
        "id": data.chassis.id,
        "name": data.chassis.name,
        "chassis_type": str(data.chassis.chassis_type),
        "manufacturer": data.chassis.manufacturer,
        "model": data.chassis.model,
        "power_state": str(data.chassis.power_state),
        "intrusion_sensor": str(data.chassis.physical_security.intrusion_sensor),
        "status_health": str(data.chassis.status.health) if data.chassis.status.health else None,
    }

    # Manager (BMC)
    coordinator_data["manager"] = {
        "id": data.manager.id,
        "name": data.manager.name,
        "manager_type": str(data.manager.manager_type),
        "firmware_version": data.manager.firmware_version,
        "model": data.manager.model,
        "status_health": str(data.manager.status.health) if data.manager.status.health else None,
    }

    # Thermal
    coordinator_data["thermal"] = {
        "temperatures": [
            {
                "member_id": t.member_id,
                "name": t.name,
                "reading_celsius": t.reading_celsius,
                "physical_context": t.physical_context,
                "status_state": str(t.status.state) if t.status.state else None,
            }
            for t in data.thermal.temperatures
        ],
        "fans": [
            {
                "member_id": f.member_id,
                "name": f.name,
                "reading_rpm": f.reading_rpm,
                "physical_context": f.physical_context,
                "status_state": str(f.status.state) if f.status.state else None,
            }
            for f in data.thermal.fans
        ],
    }

    # Power
    coordinator_data["power"] = {
        "total_power_consumed_watts": data.power.total_power_consumed_watts,
        "voltages": [
            {
                "member_id": v.member_id,
                "name": v.name,
                "reading_volts": v.reading_volts,
                "status_state": str(v.status.state) if v.status.state else None,
            }
            for v in data.power.voltages
        ],
        "power_supplies": [
            {
                "member_id": ps.member_id,
                "name": ps.name,
                "power_capacity_watts": ps.power_capacity_watts,
                "status_state": str(ps.status.state) if ps.status.state else None,
            }
            for ps in data.power.power_supplies
        ],
        "battery": {
            "health": data.power.battery.health,
            "state": data.power.battery.state,
        } if data.power.battery else None,
    }

    # OEM
    coordinator_data["oem"] = {
        "fan_mode": {
            "mode": str(data.fan_mode.mode),
            "available_modes": [str(m) for m in data.fan_mode.available_modes],
            "is_valid": data.fan_mode.is_valid,
        },
        "ntp": {
            "enabled": data.ntp.enabled,
            "primary_server": data.ntp.primary_server,
            "secondary_server": data.ntp.secondary_server,
            "is_valid": data.ntp.is_valid,
        },
        "lldp": {
            "enabled": data.lldp.enabled,
            "is_valid": data.lldp.is_valid,
        },
        "snooping": {
            "post_code": data.snooping.post_code,
            "is_valid": data.snooping.is_valid,
        },
        "license": {
            "is_licensed": data.license.is_licensed,
            "license_count": len(data.license.licenses),
            "is_valid": data.license.is_valid,
        },
    }

    # Network Protocol
    coordinator_data["network_protocol"] = {
        "hostname": data.network_protocol.hostname,
        "http_enabled": data.network_protocol.http.protocol_enabled,
        "http_port": data.network_protocol.http.port,
        "https_enabled": data.network_protocol.https.protocol_enabled,
        "https_port": data.network_protocol.https.port,
        "ssh_enabled": data.network_protocol.ssh.protocol_enabled,
        "ssh_port": data.network_protocol.ssh.port,
        "ipmi_enabled": data.network_protocol.ipmi.protocol_enabled,
        "ipmi_port": data.network_protocol.ipmi.port,
        "snmp_enabled": data.network_protocol.snmp.protocol_enabled,
        "snmp_port": data.network_protocol.snmp.port,
    }

    # Client stats
    stats = client.stats
    client_stats = {
        "total_requests": stats.total_requests,
        "cache_hits": stats.cache_hits,
        "errors": stats.errors,
        "avg_response_time_ms": round(stats.avg_response_time_ms, 2),
        "cache_hit_rate": round(stats.cache_hit_rate, 2),
    }

    return async_redact_data(
        {
            "entry": {
                "entry_id": entry.entry_id,
                "version": entry.version,
                "domain": entry.domain,
                "title": entry.title,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "coordinator_data": coordinator_data,
            "client_stats": client_stats,
        },
        TO_REDACT,
    )
