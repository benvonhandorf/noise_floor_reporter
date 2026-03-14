"""Command-line interface for noise floor reporter."""

import argparse
import logging
import sys
from typing import List, Dict, Any
from pathlib import Path
import json

from noise_floor_reporter.measure import NoiseFloorMeasurement
from noise_floor_reporter.report import NoiseFloorReporter


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config file {config_path}: {e}")
        raise


def parse_frequency_ranges(ranges: List[str]) -> List[float]:
    """Parse frequency range specifications.

    Args:
        ranges: List of frequency specifications (e.g., "144-148" or "433.5")

    Returns:
        List of frequencies in Hz
    """
    frequencies = []

    for r in ranges:
        if "-" in r:
            # Range specification
            start, end = r.split("-")
            start_mhz = float(start)
            end_mhz = float(end)
            # Sample every 1 MHz in range
            step = 1.0
            freq = start_mhz
            while freq <= end_mhz:
                frequencies.append(freq * 1e6)
                freq += step
        else:
            # Single frequency
            frequencies.append(float(r) * 1e6)

    return frequencies


def merge_config(args: argparse.Namespace, config: Dict[str, Any]) -> argparse.Namespace:
    """Merge command-line args with config file, preferring CLI args.

    Args:
        args: Command-line arguments
        config: Configuration dictionary

    Returns:
        Merged configuration as Namespace
    """
    # Start with config file defaults
    merged = argparse.Namespace(**config)

    # Override with any CLI args that were explicitly provided
    for key, value in vars(args).items():
        # Check if this was explicitly set on command line (not just default)
        if value is not None and (not hasattr(merged, key) or args.__dict__.get(key) != parser_defaults.get(key)):
            setattr(merged, key, value)

    return merged


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Measure and report SDR noise floor across multiple bands"
    )

    # Configuration file
    parser.add_argument(
        "-c", "--config", help="Path to JSON configuration file"
    )

    # SDR configuration
    parser.add_argument(
        "--backend",
        choices=["rtlsdr", "hackrf", "sdrplay", "soapysdr"],
        default="rtlsdr",
        help="SDR backend to use",
    )
    parser.add_argument("--device", type=int, default=0, help="SDR device index")
    parser.add_argument(
        "--device-args",
        help="SoapySDR device arguments (e.g., 'driver=remote,remote=192.168.1.100')",
    )
    parser.add_argument(
        "--gain", default="auto", help="SDR gain setting (auto or numeric value)"
    )
    parser.add_argument(
        "--sample-rate", type=float, default=2.4e6, help="Sample rate in Hz"
    )
    parser.add_argument(
        "--num-samples", type=int, default=256 * 1024, help="Number of samples per measurement"
    )

    # Frequency configuration
    parser.add_argument(
        "--freq",
        action="append",
        help="Frequency or range in MHz (e.g., 144-148 or 433.5). Can be specified multiple times.",
    )
    parser.add_argument(
        "--dwell", type=float, default=1.0, help="Dwell time at each frequency (seconds)"
    )

    # Output configuration
    parser.add_argument("--output-dir", default="data", help="Output directory for reports")
    parser.add_argument("--json", action="store_true", help="Save output as JSON")
    parser.add_argument("--csv", action="store_true", help="Save output as CSV")

    # MQTT configuration
    parser.add_argument("--mqtt-broker", help="MQTT broker hostname/IP")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--mqtt-topic", default="sdr/noise_floor", help="MQTT topic to publish to"
    )
    parser.add_argument("--mqtt-username", help="MQTT username")
    parser.add_argument("--mqtt-password", help="MQTT password")

    # Logging
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # Store defaults for later comparison
    global parser_defaults
    parser_defaults = {
        action.dest: action.default
        for action in parser._actions
        if action.dest != "help"
    }

    args = parser.parse_args()

    # Load and merge config file if provided
    if args.config:
        config = load_config_file(args.config)
        # Apply config file settings for any args not explicitly set on CLI
        for key, value in config.items():
            # Convert kebab-case to snake_case for argument names
            arg_key = key.replace("-", "_")
            if not hasattr(args, arg_key) or getattr(args, arg_key) == parser_defaults.get(arg_key):
                setattr(args, arg_key, value)

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Parse frequencies
        if not args.freq:
            logger.error("No frequencies specified. Use --freq or provide in config file.")
            return 1

        frequencies = parse_frequency_ranges(args.freq)
        logger.info(f"Measuring {len(frequencies)} frequencies")

        # Initialize measurement
        measurement = NoiseFloorMeasurement(
            sample_rate=args.sample_rate, num_samples=args.num_samples
        )

        try:
            gain = float(args.gain)
        except (ValueError, TypeError):
            gain = args.gain

        # Get device_args if provided
        device_args = getattr(args, "device_args", None)

        measurement.initialize_sdr(
            backend=args.backend, device_index=args.device, gain=gain, device_args=device_args
        )

        # Perform measurements
        logger.info("Starting measurements...")
        results = measurement.measure_multiple_bands(frequencies, dwell_time=args.dwell)

        # Initialize reporter
        reporter = NoiseFloorReporter(
            output_dir=args.output_dir,
            mqtt_broker=args.mqtt_broker,
            mqtt_port=args.mqtt_port,
            mqtt_topic=args.mqtt_topic,
            mqtt_username=args.mqtt_username,
            mqtt_password=args.mqtt_password,
        )

        # Save results
        if args.json:
            reporter.save_json(results)

        if args.csv:
            reporter.save_csv(results)

        # Publish to MQTT if configured
        if args.mqtt_broker:
            reporter.publish_measurements_mqtt(results)

        # Print summary
        reporter.print_summary(results)

        # Cleanup
        measurement.close()
        reporter.close()

        logger.info("Measurement complete")
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
