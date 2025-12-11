"""Reporting module for noise floor measurements."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NoiseFloorReporter:
    """Generates reports from noise floor measurements."""

    def __init__(
        self,
        output_dir: str = "data",
        mqtt_broker: Optional[str] = None,
        mqtt_port: int = 1883,
        mqtt_topic: str = "sdr/noise_floor",
        mqtt_username: Optional[str] = None,
        mqtt_password: Optional[str] = None,
    ):
        """Initialize the reporter.

        Args:
            output_dir: Directory to save reports
            mqtt_broker: MQTT broker hostname/IP (None to disable MQTT)
            mqtt_port: MQTT broker port
            mqtt_topic: MQTT topic to publish to
            mqtt_username: MQTT username (optional)
            mqtt_password: MQTT password (optional)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.mqtt_client = None

        if mqtt_broker:
            self._initialize_mqtt()

    def _initialize_mqtt(self) -> None:
        """Initialize MQTT client connection."""
        try:
            import paho.mqtt.client as mqtt

            self.mqtt_client = mqtt.Client()

            if self.mqtt_username and self.mqtt_password:
                self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)

            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
        except ImportError:
            logger.error("paho-mqtt library not installed. MQTT publishing disabled.")
            self.mqtt_client = None
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.mqtt_client = None

    def publish_mqtt(self, measurement: Dict[str, float]) -> bool:
        """Publish a single measurement to MQTT.

        Args:
            measurement: Measurement dictionary

        Returns:
            True if published successfully, False otherwise
        """
        if self.mqtt_client is None:
            logger.warning("MQTT not initialized, skipping publish")
            return False

        try:
            payload = json.dumps(measurement)
            result = self.mqtt_client.publish(self.mqtt_topic, payload, qos=1)

            if result.rc == 0:
                logger.debug(f"Published to MQTT topic {self.mqtt_topic}")
                return True
            else:
                logger.error(f"Failed to publish to MQTT: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            return False

    def publish_measurements_mqtt(self, measurements: List[Dict[str, float]]) -> int:
        """Publish multiple measurements to MQTT.

        Args:
            measurements: List of measurement dictionaries

        Returns:
            Number of successfully published measurements
        """
        if self.mqtt_client is None:
            logger.warning("MQTT not initialized, skipping publish")
            return 0

        success_count = 0
        for measurement in measurements:
            if self.publish_mqtt(measurement):
                success_count += 1

        logger.info(f"Published {success_count}/{len(measurements)} measurements to MQTT")
        return success_count

    def save_json(
        self, measurements: List[Dict[str, float]], filename: Optional[str] = None
    ) -> Path:
        """Save measurements to JSON file.

        Args:
            measurements: List of measurement dictionaries
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"noise_floor_{timestamp}.json"

        output_path = self.output_dir / filename

        try:
            with open(output_path, "w") as f:
                json.dump(measurements, f, indent=2)
            logger.info(f"Saved JSON report to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save JSON report: {e}")
            raise

    def save_csv(
        self, measurements: List[Dict[str, float]], filename: Optional[str] = None
    ) -> Path:
        """Save measurements to CSV file.

        Args:
            measurements: List of measurement dictionaries
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"noise_floor_{timestamp}.csv"

        output_path = self.output_dir / filename

        try:
            if not measurements:
                logger.warning("No measurements to save")
                return output_path

            fieldnames = list(measurements[0].keys())

            with open(output_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(measurements)

            logger.info(f"Saved CSV report to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save CSV report: {e}")
            raise

    def generate_summary(self, measurements: List[Dict[str, float]]) -> Dict[str, float]:
        """Generate summary statistics from measurements.

        Args:
            measurements: List of measurement dictionaries

        Returns:
            Dictionary containing summary statistics
        """
        if not measurements:
            return {}

        import numpy as np

        mean_values = [m["mean_dbfs"] for m in measurements]
        median_values = [m["median_dbfs"] for m in measurements]

        summary = {
            "total_measurements": len(measurements),
            "overall_mean_dbfs": float(np.mean(mean_values)),
            "overall_median_dbfs": float(np.median(median_values)),
            "overall_min_dbfs": float(np.min([m["min_dbfs"] for m in measurements])),
            "overall_max_dbfs": float(np.max([m["max_dbfs"] for m in measurements])),
            "mean_std_dbfs": float(np.std(mean_values)),
        }

        return summary

    def print_summary(self, measurements: List[Dict[str, float]]) -> None:
        """Print summary statistics to console.

        Args:
            measurements: List of measurement dictionaries
        """
        summary = self.generate_summary(measurements)

        print("\n" + "=" * 60)
        print("NOISE FLOOR MEASUREMENT SUMMARY")
        print("=" * 60)
        print(f"Total measurements: {summary['total_measurements']}")
        print(f"Overall mean:       {summary['overall_mean_dbfs']:.2f} dBFS")
        print(f"Overall median:     {summary['overall_median_dbfs']:.2f} dBFS")
        print(f"Overall min:        {summary['overall_min_dbfs']:.2f} dBFS")
        print(f"Overall max:        {summary['overall_max_dbfs']:.2f} dBFS")
        print(f"Std deviation:      {summary['mean_std_dbfs']:.2f} dBFS")
        print("=" * 60 + "\n")

    def close(self) -> None:
        """Close connections and cleanup resources."""
        if self.mqtt_client is not None:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT: {e}")
