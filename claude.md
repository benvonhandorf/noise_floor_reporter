# Noise Floor Reporter - Developer Documentation

## Project Overview

`noise_floor_reporter` is a Python application for measuring and reporting the noise floor of Software Defined Radios (SDRs) across multiple frequency bands over time. It supports multiple SDR backends, including network-accessible SDRs via SoapySDR Remote protocol.

## Quick Start

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/noise_floor_reporter.git
cd noise_floor_reporter

# Create and activate virtual environment (RECOMMENDED)
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# For development with all dependencies
pip install -e ".[dev,soapysdr]"
```

### Running the Tool

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run with RTL-SDR
noise-floor-reporter --freq 7.0-7.3 --freq 14.0-14.35 --json

# Run with remote SoapySDR
noise-floor-reporter --backend soapysdr \
  --device-args "driver=remote,remote=192.168.1.100" \
  --freq 7.0-7.3 --json

# Deactivate when done
deactivate
```

## Architecture

### Core Modules

```
noise_floor_reporter/
├── __init__.py              # Package initialization
├── backends/                # SDR backend implementations
│   ├── __init__.py         # Backend exports
│   ├── base.py             # SDRBackend Protocol
│   ├── rtlsdr.py           # RTL-SDR backend
│   ├── hackrf.py           # HackRF backend
│   ├── sdrplay.py          # SDRPlay backend
│   └── soapysdr.py         # SoapySDR backend (network support)
├── measure.py              # Noise floor measurement logic
├── report.py               # Output formatting and MQTT publishing
└── cli.py                  # Command-line interface
```

### Design Patterns

**Backend Protocol**: All SDR backends implement the `SDRBackend` Protocol defined in `backends/base.py`:
- `set_sample_rate(rate: float) -> None`
- `set_center_frequency(freq: float) -> None`
- `set_gain(gain: str | float) -> None`
- `read_samples(num_samples: int) -> np.ndarray`
- `close() -> None`

**Factory Pattern**: `NoiseFloorMeasurement` class uses a dictionary-based factory to instantiate backends based on user selection.

**Separation of Concerns**:
- `backends/` - Hardware abstraction
- `measure.py` - Measurement logic
- `report.py` - Output and publishing
- `cli.py` - User interface

## Key Components

### 1. SDR Backends (`backends/`)

Each backend is self-contained and implements hardware-specific communication.

**RTL-SDR Backend** (`rtlsdr.py`)
- Uses `pyrtlsdr` library
- Simple gain control (auto or manual)
- Most common and widely supported

**HackRF Backend** (`hackrf.py`)
- Uses `hackrf` library
- LNA gain control
- Default gain: 20 dB when "auto" specified

**SDRPlay Backend** (`sdrplay.py`)
- Uses `sdrplay` library
- AGC support
- Requires SDRPlay API drivers

**SoapySDR Backend** (`soapysdr.py`)
- Uses `SoapySDR` library
- Supports network protocol via `driver=remote,remote=IP:PORT`
- Stream-based architecture (setup, activate, read, deactivate, close)
- Device arguments parsing for flexible configuration
- Hardware-agnostic (works with any SoapySDR-supported device)

### 2. Measurement Module (`measure.py`)

**NoiseFloorMeasurement Class**
- Manages SDR initialization and configuration
- Performs FFT-based power spectrum analysis
- Calculates statistics: mean, median, min, max, std deviation
- Supports sequential multi-band measurements

**Key Methods**:
- `initialize_sdr()` - Factory method for backend selection
- `measure_band()` - Single frequency measurement
- `measure_multiple_bands()` - Sequential band scanning
- `close()` - Clean resource cleanup

**Measurement Process**:
1. Set center frequency
2. Read IQ samples from SDR
3. Compute FFT
4. Calculate power spectral density (PSD) in dBFS
5. Generate statistics
6. Return results dictionary

### 3. Reporting Module (`report.py`)

**NoiseFloorReporter Class**
- JSON export
- CSV export
- Real-time MQTT publishing
- Summary statistics generation

**MQTT Integration**:
- Connects to MQTT broker on initialization
- Publishes measurements as JSON payloads
- Supports authentication (username/password)
- QoS level 1 for reliable delivery
- Auto-reconnect via paho-mqtt client

### 4. CLI Module (`cli.py`)

**Configuration**:
- Command-line arguments (highest priority)
- JSON configuration file
- Sensible defaults

**Frequency Parsing**:
- Range notation: `7.0-7.3` (generates 1 MHz steps)
- Single frequency: `14.070`
- Multiple specifications: `--freq 7.0-7.3 --freq 14.0-14.35`

**Configuration Merging**:
- CLI args override config file values
- Config file provides defaults

## Data Flow

```
User Input (CLI/Config)
    ↓
NoiseFloorMeasurement
    ↓
SDR Backend Selection
    ↓
Backend Initialization
    ↓
For each frequency:
    Set Frequency → Read Samples → FFT → Calculate Stats
    ↓
Results List
    ↓
NoiseFloorReporter
    ├→ Save JSON
    ├→ Save CSV
    ├→ Publish MQTT
    └→ Print Summary
```

## Configuration

### CLI Arguments

Key parameters:
- `--backend`: SDR backend selection (`rtlsdr`, `hackrf`, `sdrplay`, `soapysdr`)
- `--device-args`: SoapySDR device arguments for network or specific device selection
- `--freq`: Frequency specification (MHz)
- `--sample-rate`: Sample rate (Hz)
- `--num-samples`: Samples per measurement
- `--dwell`: Settling time per frequency (seconds)
- `--mqtt-broker`: MQTT broker hostname for real-time publishing

### JSON Configuration

Example structure:
```json
{
  "backend": "soapysdr",
  "device_args": "driver=remote,remote=192.168.1.100",
  "freq": ["3.5-4.0", "7.0-7.3"],
  "sample_rate": 2400000,
  "mqtt_broker": "mqtt.example.com"
}
```

### Environment Considerations

**HF Amateur Radio Bands** (default config):
- 80m: 3.5-4.0 MHz
- 40m: 7.0-7.3 MHz
- 30m: 10.1-10.15 MHz
- 20m: 14.0-14.35 MHz
- 17m: 18.068-18.168 MHz
- 15m: 21.0-21.45 MHz
- 12m: 24.89-24.99 MHz
- 10m: 28.0-29.7 MHz

## Network Protocol (SoapySDR Remote)

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  noise_floor_   │  TCP    │  SoapySDRServer │
│  reporter       │◄───────►│  (Port 55132)   │
│  (Client)       │         │                 │
└─────────────────┘         └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │   SDR Hardware  │
                            │  (RTL-SDR, etc) │
                            └─────────────────┘
```

### Use Cases

1. **Remote Monitoring**: Monitor RF environment from centralized location
2. **Embedded Devices**: Access SDRs on Raspberry Pi without local processing
3. **Resource Sharing**: Multiple applications accessing same SDR hardware
4. **Network Isolation**: SDR in RF-shielded environment, processing elsewhere

### Device Arguments Format

SoapySDR uses comma-separated key=value pairs:
- `driver=remote,remote=192.168.1.100` - Remote SDR
- `driver=remote,remote=192.168.1.100:55133` - Custom port
- `driver=rtlsdr,serial=00000001` - Specific local device
- `driver=hackrf` - Local HackRF

## Output Formats

### Measurement Result Schema

```python
{
    "timestamp": str,        # ISO 8601 UTC timestamp
    "center_freq": float,    # Hz
    "bandwidth": float,      # Hz
    "mean_dbfs": float,      # Mean power (dBFS)
    "median_dbfs": float,    # Median power (dBFS)
    "min_dbfs": float,       # Minimum power (dBFS)
    "max_dbfs": float,       # Maximum power (dBFS)
    "std_dbfs": float        # Standard deviation (dBFS)
}
```

### JSON Output

Array of measurement objects, saved to `data/noise_floor_TIMESTAMP.json`

### CSV Output

Tabular format with columns matching measurement schema, saved to `data/noise_floor_TIMESTAMP.csv`

### MQTT Messages

Published to configured topic (default: `sdr/noise_floor`) as individual JSON messages per measurement.

## Adding New Backends

1. Create new file in `backends/` (e.g., `backends/mydevice.py`)
2. Implement `SDRBackend` Protocol:
   ```python
   class MyDeviceBackend:
       def __init__(self, device_index: int = 0):
           # Initialize hardware

       def set_sample_rate(self, rate: float) -> None:
           # Set sample rate

       def set_center_frequency(self, freq: float) -> None:
           # Set frequency

       def set_gain(self, gain: str | float) -> None:
           # Set gain (handle "auto" string)

       def read_samples(self, num_samples: int) -> np.ndarray:
           # Return complex samples

       def close(self) -> None:
           # Cleanup
   ```

3. Export in `backends/__init__.py`:
   ```python
   from noise_floor_reporter.backends.mydevice import MyDeviceBackend
   __all__ = [..., "MyDeviceBackend"]
   ```

4. Register in `measure.py`:
   ```python
   BACKENDS = {
       ...
       "mydevice": MyDeviceBackend,
   }
   ```

5. Update CLI choices in `cli.py`:
   ```python
   choices=["rtlsdr", "hackrf", "sdrplay", "soapysdr", "mydevice"]
   ```

## Testing Strategy

### Unit Tests (Recommended)

- Mock backend implementations
- Test measurement calculations with synthetic data
- Verify configuration parsing and merging
- Test frequency range expansion

### Integration Tests

- Test with SDR hardware or simulators
- Verify output file generation
- Test MQTT publishing (use test broker)
- Validate network protocol with SoapySDR Remote

### Example Mock Backend

```python
class MockBackend:
    def __init__(self, device_index: int = 0):
        self.sample_rate = 2.4e6
        self.center_freq = 100e6

    def read_samples(self, num_samples: int) -> np.ndarray:
        # Return synthetic noise
        return np.random.randn(num_samples) + 1j * np.random.randn(num_samples)

    # Implement other Protocol methods...
```

## Dependencies

### Virtual Environment (Recommended)

**Always use a virtual environment** to isolate project dependencies:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install project
pip install -e .

# Deactivate when done
deactivate
```

**Benefits:**
- Isolated dependencies per project
- No conflicts with system Python packages
- Easy to reproduce environment
- Safe experimentation

**Note:** The `.venv/` directory is already in `.gitignore` and will not be committed.

### Required Dependencies
- `numpy>=1.24.0` - FFT and statistics
- `matplotlib>=3.7.0` - Future plotting support
- `pyrtlsdr>=0.2.93` - RTL-SDR backend (optional for other backends)
- `paho-mqtt>=1.6.1` - MQTT publishing

### Optional (Backend-Specific)
- `SoapySDR>=0.8.0` - SoapySDR backend
- `hackrf` - HackRF backend
- `sdrplay` - SDRPlay backend

### Installation Combinations

```bash
# Base installation (RTL-SDR only)
pip install -e .

# With SoapySDR support
pip install -e ".[soapysdr]"

# With development tools
pip install -e ".[dev]"

# Everything (development + SoapySDR)
pip install -e ".[dev,soapysdr]"
```

## Performance Considerations

### Sample Size vs Speed
- Default: 256K samples (~107ms at 2.4 MSPS)
- Larger samples = better frequency resolution, slower
- Smaller samples = faster scanning, less resolution

### Dwell Time
- Allow SDR to settle after frequency change
- Default 1 second may be excessive for some applications
- Modern SDRs can settle in 10-100ms

### Network Latency (SoapySDR Remote)
- TCP overhead adds latency
- Consider local buffering
- QoS on network for real-time measurements

## Common Issues

### Import Errors
- Ensure backend libraries installed: `pip install pyrtlsdr`
- For SoapySDR: `pip install -e ".[soapysdr]"`

### Device Access
- RTL-SDR may require udev rules on Linux
- HackRF requires permissions: add user to `plugdev` group
- SoapySDR remote requires network access to server

### Frequency Range Limitations
- RTL-SDR: ~24-1766 MHz (with direct sampling: 0.5-24 MHz)
- HackRF: 1 MHz - 6 GHz
- Device-specific limitations apply

### MQTT Connection Failures
- Verify broker hostname and port
- Check authentication credentials
- Ensure network connectivity

## Future Enhancements

### Potential Features
- Real-time plotting with matplotlib
- Frequency hopping detection
- Waterfall displays
- Historical trend analysis
- Web interface for remote monitoring
- Docker containerization
- Systemd service file
- Database storage (PostgreSQL, InfluxDB)
- Grafana dashboard integration

### Backend Additions
- LimeSDR support
- AirSpy support
- Perseus SDR support
- WebSDR integration

## Code Style

- **Formatting**: Black with 100-char line length
- **Linting**: Ruff
- **Type Hints**: Python 3.9+ style (PEP 604: `str | float`)
- **Docstrings**: Google style
- **Logging**: Use module-level logger

## Version History

### 0.1.0 (Current)
- Initial implementation
- Multiple SDR backend support (RTL-SDR, HackRF, SDRPlay, SoapySDR)
- SoapySDR network protocol support
- JSON/CSV/MQTT output
- Configuration file support
- HF amateur radio band defaults
- Modular backend architecture

## Contributing

When adding features:
1. Follow existing code structure
2. Implement proper logging
3. Add docstrings
4. Update this documentation
5. Consider backwards compatibility
6. Test with actual hardware when possible

## License

MIT License (or as specified in project)

## Contact & Support

For issues and feature requests, use the project's GitHub issue tracker.

---

*Last updated: 2025-12-11*
*Project initialized with Claude Code*
