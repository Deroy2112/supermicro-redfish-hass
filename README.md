# Supermicro Redfish Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Deroy2112/supermicro-redfish-hass)](https://github.com/Deroy2112/supermicro-redfish-hass/releases)
[![License](https://img.shields.io/github/license/Deroy2112/supermicro-redfish-hass)](LICENSE)

Home Assistant custom integration for monitoring and controlling Supermicro servers via the Redfish API.

## Features

- **System Monitoring**: Power state, health status, temperatures, fan speeds, voltages
- **Power Control**: Power on/off, graceful shutdown, restart, BMC restart
- **Configuration**: Fan mode, boot source, indicator LED, network protocols
- **Diagnostics**: BIOS version, BMC firmware, POST code, API response time
- **Adaptive Polling**: Burst mode for faster updates after user actions

## Supported Devices

This integration supports Supermicro servers with BMC (Baseboard Management Controller) that implements the Redfish API. Tested with:

- X11/X12/X13 series motherboards
- BMC firmware with Redfish support

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → "Custom repositories"
3. Add `https://github.com/Deroy2112/supermicro-redfish-hass` as an "Integration"
4. Search for "Supermicro Redfish" and install
5. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy `custom_components/supermicro_redfish` to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Supermicro Redfish"
3. Enter your BMC connection details:
   - **Host**: BMC IP address or hostname
   - **Username**: BMC username (e.g., ADMIN)
   - **Password**: BMC password
   - **Verify SSL**: Enable if using valid SSL certificates

## Entities

### Binary Sensors

| Entity | Description |
|--------|-------------|
| System Power | Server power state (on/off) |
| System Health Problem | System health is not OK |
| Chassis Health Problem | Chassis health is not OK |
| BMC Health Problem | BMC health is not OK |
| Chassis Intrusion | Chassis cover has been opened |
| License Active | BMC license is active |
| CMOS Battery Problem | CMOS battery needs replacement |
| NTP Enabled | NTP time sync is enabled |
| LLDP Enabled | LLDP protocol is enabled |

### Sensors

| Entity | Description |
|--------|-------------|
| Power Consumption | Total power usage (Watts) |
| BIOS Version | Current BIOS version |
| BMC Firmware | BMC firmware version |
| POST Code | Current POST diagnostic code |
| API Response Time | Average API response time (ms) |
| CPU Temperature (N) | CPU temperature readings |
| System Temperature (N) | System temperature readings |
| Fan Speed (N) | Fan speed readings (RPM) |
| Voltage (N) | Voltage readings |

### Buttons

| Entity | Description |
|--------|-------------|
| Power On | Turn on the server |
| Power Off | Force power off |
| Graceful Shutdown | Request OS shutdown |
| Graceful Restart | Request OS restart |
| Force Restart | Force immediate restart |
| BMC Restart | Restart the BMC |
| Send NMI | Send Non-Maskable Interrupt |
| Reset Intrusion | Reset chassis intrusion sensor |

### Switches

| Entity | Description |
|--------|-------------|
| Indicator LED | System identification LED |
| HTTP Protocol | Enable/disable HTTP on BMC |
| SSH Protocol | Enable/disable SSH on BMC |
| IPMI Protocol | Enable/disable IPMI on BMC |
| SNMP Protocol | Enable/disable SNMP on BMC |

### Selects

| Entity | Description |
|--------|-------------|
| Fan Mode | Fan control mode (Standard, Full Speed, Optimal, Heavy I/O) |
| Boot Source | Next boot device override |

## Options

Configure polling intervals in the integration options:

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| Scan Interval | 30s | 10-300s | Normal polling interval |
| Burst Interval | 5s | 1-30s | Fast polling after actions |
| Burst Duration | 60s | 10-300s | How long burst mode lasts |
| Static Interval | 300s | 60-900s | Interval for static data (BIOS, firmware) |
| Max Concurrent Requests | 5 | 1-10 | Parallel API requests limit |

## Troubleshooting

### Cannot Connect

- Verify the BMC IP address is correct and reachable
- Check that the Redfish API is enabled in BMC settings
- Ensure the username/password are correct
- Try disabling SSL verification if using self-signed certificates

### Authentication Failed

- Verify credentials are correct
- Check if the account is locked due to failed attempts
- Ensure the user has sufficient privileges

### Entities Unavailable

- Check BMC connectivity
- Some features may not be available on all BMC versions
- OEM features (fan mode, NTP, LLDP) require specific firmware

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/Deroy2112/supermicro-redfish-hass.git
cd supermicro-redfish-hass

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=custom_components/supermicro_redfish --cov-report=term-missing

# Type checking
mypy custom_components/supermicro_redfish --strict

# Linting
ruff check custom_components/supermicro_redfish
```

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

- Uses [supermicro-redfish-client](https://pypi.org/project/supermicro-redfish-client/) for API communication
- Built for [Home Assistant](https://www.home-assistant.io/)
