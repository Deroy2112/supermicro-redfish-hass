"""Constants for the Supermicro Redfish integration."""

from __future__ import annotations

from typing import Final

# Domain
DOMAIN: Final = "supermicro_redfish"

# Configuration keys
CONF_VERIFY_SSL: Final = "verify_ssl"

# Polling intervals (seconds)
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_BURST_INTERVAL: Final = 5
DEFAULT_BURST_DURATION: Final = 60
DEFAULT_STATIC_INTERVAL: Final = 300

# Option keys
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_BURST_INTERVAL: Final = "burst_interval"
CONF_BURST_DURATION: Final = "burst_duration"
CONF_STATIC_INTERVAL: Final = "static_interval"
CONF_MAX_CONCURRENT_REQUESTS: Final = "max_concurrent_requests"

# Option ranges
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 300
MIN_BURST_INTERVAL: Final = 1
MAX_BURST_INTERVAL: Final = 30
MIN_BURST_DURATION: Final = 10
MAX_BURST_DURATION: Final = 300
MIN_STATIC_INTERVAL: Final = 60
MAX_STATIC_INTERVAL: Final = 900
MIN_CONCURRENT_REQUESTS: Final = 1
MAX_CONCURRENT_REQUESTS: Final = 10
DEFAULT_CONCURRENT_REQUESTS: Final = 5

# Connection error threshold for repair issue
CONNECTION_ERROR_THRESHOLD: Final = 3

# Entity keys for unique identification
ENTITY_KEY_SYSTEM_POWER: Final = "system_power"
ENTITY_KEY_SYSTEM_HEALTH: Final = "system_health"
ENTITY_KEY_CHASSIS_HEALTH: Final = "chassis_health"
ENTITY_KEY_BMC_HEALTH: Final = "bmc_health"
ENTITY_KEY_INTRUSION: Final = "intrusion"
ENTITY_KEY_LICENSE: Final = "license_active"
ENTITY_KEY_CMOS_BATTERY: Final = "cmos_battery"
ENTITY_KEY_NTP_ENABLED: Final = "ntp_enabled"
ENTITY_KEY_LLDP_ENABLED: Final = "lldp_enabled"

ENTITY_KEY_POWER_CONSUMPTION: Final = "power_consumption"
ENTITY_KEY_BIOS_VERSION: Final = "bios_version"
ENTITY_KEY_BMC_FIRMWARE: Final = "bmc_firmware"
ENTITY_KEY_POST_CODE: Final = "post_code"
ENTITY_KEY_API_RESPONSE_TIME: Final = "api_response_time"

ENTITY_KEY_INDICATOR_LED: Final = "indicator_led"
ENTITY_KEY_HTTP_PROTOCOL: Final = "http_protocol"
ENTITY_KEY_SSH_PROTOCOL: Final = "ssh_protocol"
ENTITY_KEY_IPMI_PROTOCOL: Final = "ipmi_protocol"
ENTITY_KEY_SNMP_PROTOCOL: Final = "snmp_protocol"

ENTITY_KEY_FAN_MODE: Final = "fan_mode"
ENTITY_KEY_BOOT_SOURCE: Final = "boot_source"

ENTITY_KEY_POWER_ON: Final = "power_on"
ENTITY_KEY_POWER_OFF: Final = "power_off"
ENTITY_KEY_GRACEFUL_SHUTDOWN: Final = "graceful_shutdown"
ENTITY_KEY_GRACEFUL_RESTART: Final = "graceful_restart"
ENTITY_KEY_FORCE_RESTART: Final = "force_restart"
ENTITY_KEY_BMC_RESTART: Final = "bmc_restart"
ENTITY_KEY_SEND_NMI: Final = "send_nmi"
ENTITY_KEY_RESET_INTRUSION: Final = "reset_intrusion"

# Platforms
PLATFORMS: Final = [
    "binary_sensor",
    "sensor",
    "button",
    "switch",
    "select",
]
