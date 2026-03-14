"""Noise floor measurement module for SDR."""

import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
import logging

from noise_floor_reporter.backends import (
    SDRBackend,
    RTLSDRBackend,
    HackRFBackend,
    SDRPlayBackend,
    SoapySDRBackend,
)

logger = logging.getLogger(__name__)


class NoiseFloorMeasurement:
    """Measures noise floor across specified frequency bands."""

    BACKENDS = {
        "rtlsdr": RTLSDRBackend,
        "hackrf": HackRFBackend,
        "sdrplay": SDRPlayBackend,
        "soapysdr": SoapySDRBackend,
    }

    def __init__(self, sample_rate: int = 2.4e6, num_samples: int = 256 * 1024):
        """Initialize the noise floor measurement.

        Args:
            sample_rate: SDR sample rate in Hz
            num_samples: Number of samples to collect per measurement
        """
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.sdr: Optional[SDRBackend] = None

    def initialize_sdr(
        self,
        backend: str = "rtlsdr",
        device_index: int = 0,
        gain: str | float = "auto",
        device_args: Optional[str] = None,
    ) -> None:
        """Initialize the SDR device with specified backend.

        Args:
            backend: SDR backend to use ('rtlsdr', 'hackrf', 'sdrplay', 'soapysdr')
            device_index: Index of the SDR device
            gain: Gain setting ('auto' or specific value)
            device_args: SoapySDR device arguments string (only for soapysdr backend)
                        Example: "driver=remote,remote=192.168.1.100"
        """
        if backend not in self.BACKENDS:
            raise ValueError(
                f"Unknown backend '{backend}'. Available: {list(self.BACKENDS.keys())}"
            )

        try:
            backend_class = self.BACKENDS[backend]

            # SoapySDR backend supports device_args
            if backend == "soapysdr":
                self.sdr = backend_class(device_index, device_args)
            else:
                self.sdr = backend_class(device_index)

            self.sdr.set_sample_rate(self.sample_rate)
            self.sdr.set_gain(gain)
            logger.info(f"Initialized {backend} device {device_index}")
        except Exception as e:
            logger.error(f"Failed to initialize SDR backend '{backend}': {e}")
            raise

    def measure_band(
        self, center_freq: float, bandwidth: Optional[float] = None
    ) -> Dict[str, float]:
        """Measure noise floor for a specific frequency band.

        Args:
            center_freq: Center frequency in Hz
            bandwidth: Bandwidth to measure (defaults to sample_rate)

        Returns:
            Dictionary containing measurement results
        """
        if self.sdr is None:
            raise RuntimeError("SDR not initialized. Call initialize_sdr() first.")

        bandwidth = bandwidth or self.sample_rate

        try:
            self.sdr.set_center_frequency(center_freq)
            samples = self.sdr.read_samples(self.num_samples)

            # Calculate power spectrum
            fft = np.fft.fft(samples)
            psd = 10 * np.log10(np.abs(fft) ** 2 / len(fft))

            # Calculate statistics
            mean_power = np.mean(psd)
            median_power = np.median(psd)
            min_power = np.min(psd)
            max_power = np.max(psd)
            std_power = np.std(psd)

            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "center_freq": center_freq,
                "bandwidth": bandwidth,
                "mean_dbfs": float(mean_power),
                "median_dbfs": float(median_power),
                "min_dbfs": float(min_power),
                "max_dbfs": float(max_power),
                "std_dbfs": float(std_power),
            }

            logger.info(
                f"Measured {center_freq/1e6:.2f} MHz: "
                f"mean={mean_power:.2f} dBFS, median={median_power:.2f} dBFS"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to measure band at {center_freq/1e6:.2f} MHz: {e}")
            raise

    def measure_multiple_bands(
        self, frequency_list: List[float], dwell_time: float = 1.0
    ) -> List[Dict[str, float]]:
        """Measure noise floor across multiple frequency bands.

        Args:
            frequency_list: List of center frequencies in Hz
            dwell_time: Time to wait at each frequency before measuring

        Returns:
            List of measurement results for each frequency
        """
        import time

        results = []

        for freq in frequency_list:
            time.sleep(dwell_time)
            result = self.measure_band(freq)
            results.append(result)

        return results

    def close(self) -> None:
        """Close the SDR device."""
        if self.sdr is not None:
            self.sdr.close()
            logger.info("Closed SDR device")
