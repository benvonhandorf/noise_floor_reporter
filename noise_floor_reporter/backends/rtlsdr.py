"""RTL-SDR backend implementation."""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class RTLSDRBackend:
    """RTL-SDR backend implementation."""

    def __init__(self, device_index: int = 0):
        from rtlsdr import RtlSdr

        self.sdr = RtlSdr(device_index)
        logger.info(f"Initialized RTL-SDR device {device_index}")

    def set_sample_rate(self, rate: float) -> None:
        self.sdr.sample_rate = rate

    def set_center_frequency(self, freq: float) -> None:
        self.sdr.center_freq = freq

    def set_gain(self, gain: str | float) -> None:
        self.sdr.gain = gain

    def read_samples(self, num_samples: int) -> np.ndarray:
        return self.sdr.read_samples(num_samples)

    def close(self) -> None:
        self.sdr.close()
