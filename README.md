# noise_floor_reporter

Python scripts to calculate and report on the noise floor of an SDR across multiple bands over time.

## Features

- Support for multiple SDR backends:
  - RTL-SDR
  - HackRF
  - SDRPlay
- Measure noise floor across multiple frequency bands
- Export measurements to JSON and CSV formats
- Publish measurements to MQTT broker in real-time
- Configuration via command-line arguments or JSON config file
- Comprehensive logging and statistics

## Installation

### From source

```bash
git clone https://github.com/yourusername/noise_floor_reporter.git
cd noise_floor_reporter
pip install -e .
```

### Dependencies

The main dependencies are:
- numpy
- matplotlib
- pyrtlsdr (for RTL-SDR support)
- paho-mqtt (for MQTT publishing)

Additional SDR backends require their respective Python libraries.

## Usage

### Basic usage

Measure noise floor on HF amateur bands using RTL-SDR:

```bash
noise-floor-reporter --freq 7.0-7.3 --freq 14.0-14.35 --json
```

### Using a configuration file

Create a configuration file (see [config.example.json](config.example.json)):

```bash
noise-floor-reporter -c config.json
```

### Command-line options

```
usage: noise-floor-reporter [-h] [-c CONFIG] [--backend {rtlsdr,hackrf,sdrplay}]
                           [--device DEVICE] [--gain GAIN]
                           [--sample-rate SAMPLE_RATE]
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
  --backend {rtlsdr,hackrf,sdrplay}
                        SDR backend to use
  --device DEVICE       SDR device index
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

## Development

Install development dependencies:

```bash
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

## License

MIT License (or your preferred license)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
