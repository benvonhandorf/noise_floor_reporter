# noise_floor_reporter

Python scripts to calculate and report on the noise floor of an SDR across multiple bands over time.

## Features

- Support for multiple SDR backends:
  - RTL-SDR
  - HackRF
  - SDRPlay
  - SoapySDR (with network protocol support for remote SDRs)
- Measure noise floor across multiple frequency bands
- Export measurements to JSON and CSV formats
- Publish measurements to MQTT broker in real-time
- Configuration via command-line arguments or JSON config file
- Comprehensive logging and statistics

## Installation

### Quick Setup (Linux/Mac)

```bash
git clone https://github.com/yourusername/noise_floor_reporter.git
cd noise_floor_reporter

# Run the setup script (creates venv and installs)
./setup-dev.sh
```

### Manual Setup

```bash
git clone https://github.com/yourusername/noise_floor_reporter.git
cd noise_floor_reporter

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or on Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### Dependencies

The main dependencies are:
- numpy
- matplotlib
- pyrtlsdr (for RTL-SDR support)
- paho-mqtt (for MQTT publishing)

Additional SDR backends require their respective Python libraries:
- RTL-SDR: `pip install pyrtlsdr`
- HackRF: `pip install hackrf`
- SDRPlay: `pip install sdrplay` (plus SDRPlay API drivers)
- SoapySDR: `pip install -e ".[soapysdr]"` or `pip install SoapySDR`

For SoapySDR remote access, install SoapySDR Remote on both client and server:
```bash
# On the server (where the SDR is connected)
sudo apt-get install soapysdr-server soapysdr-module-remote

# On the client (where you run this tool, inside virtual environment)
pip install -e ".[soapysdr]"
```

**Note**: Always activate the virtual environment before running the tool:
```bash
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

## Usage

### Basic usage

Measure noise floor on HF amateur bands using RTL-SDR:

```bash
noise-floor-reporter --freq 7.0-7.3 --freq 14.0-14.35 --json
```

Use SoapySDR with a remote SDR over the network:

```bash
noise-floor-reporter --backend soapysdr \
  --device-args "driver=remote,remote=192.168.1.100" \
  --freq 7.0-7.3 --json
```

Use SoapySDR with a local RTL-SDR:

```bash
noise-floor-reporter --backend soapysdr \
  --device-args "driver=rtlsdr" \
  --freq 14.0-14.35 --json
```

### Using a configuration file

Create a configuration file (see [config.example.json](config.example.json)):

```bash
noise-floor-reporter -c config.json
```

### Command-line options

```
usage: noise-floor-reporter [-h] [-c CONFIG] [--backend {rtlsdr,hackrf,sdrplay,soapysdr}]
                           [--device DEVICE] [--device-args DEVICE_ARGS]
                           [--gain GAIN] [--sample-rate SAMPLE_RATE]
                           [--num-samples NUM_SAMPLES] [--freq FREQ]
                           [--dwell DWELL] [--output-dir OUTPUT_DIR] [--json]
                           [--csv] [--mqtt-broker MQTT_BROKER]
                           [--mqtt-port MQTT_PORT] [--mqtt-topic MQTT_TOPIC]
                           [--mqtt-username MQTT_USERNAME]
                           [--mqtt-password MQTT_PASSWORD] [-v]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to JSON configuration file
  --backend {rtlsdr,hackrf,sdrplay,soapysdr}
                        SDR backend to use
  --device DEVICE       SDR device index
  --device-args DEVICE_ARGS
                        SoapySDR device arguments (e.g., 'driver=remote,remote=192.168.1.100')
  --gain GAIN           SDR gain setting (auto or numeric value)
  --sample-rate SAMPLE_RATE
                        Sample rate in Hz
  --num-samples NUM_SAMPLES
                        Number of samples per measurement
  --freq FREQ           Frequency or range in MHz (e.g., 144-148 or 433.5).
                        Can be specified multiple times.
  --dwell DWELL         Dwell time at each frequency (seconds)
  --output-dir OUTPUT_DIR
                        Output directory for reports
  --json                Save output as JSON
  --csv                 Save output as CSV
  --mqtt-broker MQTT_BROKER
                        MQTT broker hostname/IP
  --mqtt-port MQTT_PORT
                        MQTT broker port
  --mqtt-topic MQTT_TOPIC
                        MQTT topic to publish to
  --mqtt-username MQTT_USERNAME
                        MQTT username
  --mqtt-password MQTT_PASSWORD
                        MQTT password
  -v, --verbose         Enable verbose logging
```

### Configuration file format

Configuration files use JSON format:

```json
{
  "backend": "rtlsdr",
  "device": 0,
  "gain": "auto",
  "sample_rate": 2400000,
  "num_samples": 262144,
  "freq": [
    "3.5-4.0",
    "7.0-7.3",
    "14.0-14.35"
  ],
  "dwell": 1.0,
  "output_dir": "data",
  "json": true,
  "csv": true,
  "mqtt_broker": "mqtt.example.com",
  "mqtt_port": 1883,
  "mqtt_topic": "sdr/noise_floor"
}
```

### MQTT Publishing

When MQTT is configured, measurements are published in real-time as JSON messages:

```json
{
  "timestamp": "2025-12-11T12:00:00.000000",
  "center_freq": 7100000.0,
  "bandwidth": 2400000.0,
  "mean_dbfs": -45.2,
  "median_dbfs": -45.5,
  "min_dbfs": -52.1,
  "max_dbfs": -38.3,
  "std_dbfs": 2.1
}
```

## Output Format

### JSON Output

Measurements are saved as an array of measurement objects:

```json
[
  {
    "timestamp": "2025-12-11T12:00:00.000000",
    "center_freq": 7100000.0,
    "bandwidth": 2400000.0,
    "mean_dbfs": -45.2,
    "median_dbfs": -45.5,
    "min_dbfs": -52.1,
    "max_dbfs": -38.3,
    "std_dbfs": 2.1
  }
]
```

### CSV Output

Measurements are saved in CSV format with the same fields as headers.

## SoapySDR Network Protocol

SoapySDR supports accessing remote SDRs over the network using the SoapySDR Remote protocol. This allows you to:
- Monitor noise floor from a centralized server
- Access SDRs on embedded devices (Raspberry Pi, etc.)
- Share SDR hardware across multiple users/applications

### Setting up SoapySDR Remote

**On the SDR server (where the hardware is connected):**

1. Install SoapySDR and the remote server:
```bash
sudo apt-get install soapysdr-server soapysdr-module-remote
```

2. Start the SoapySDR server:
```bash
SoapySDRServer --bind=0.0.0.0:55132
```

3. (Optional) Run as a systemd service for automatic startup.

**On the client (where you run noise-floor-reporter):**

1. Install this package with SoapySDR support:
```bash
pip install -e ".[soapysdr]"
```

2. Test the connection:
```bash
SoapySDRUtil --find="driver=remote,remote=192.168.1.100"
```

3. Run measurements:
```bash
noise-floor-reporter --backend soapysdr \
  --device-args "driver=remote,remote=192.168.1.100" \
  --freq 7.0-7.3 --json
```

### SoapySDR Device Arguments

Common device argument patterns:

- Remote SDR: `driver=remote,remote=192.168.1.100`
- Remote with custom port: `driver=remote,remote=192.168.1.100:55133`
- Local RTL-SDR via SoapySDR: `driver=rtlsdr`
- Local HackRF via SoapySDR: `driver=hackrf`
- Specific device by serial: `driver=rtlsdr,serial=00000001`

## Development

Set up development environment:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install package with development dependencies
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Format code:

```bash
black noise_floor_reporter
ruff check noise_floor_reporter
```

Deactivate virtual environment when done:

```bash
deactivate
```

## License

MIT License (or your preferred license)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
