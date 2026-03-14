"""HackRF backend implementation."""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class HackRFBackend:
    """HackRF backend implementation."""

    def __init__(self, device_index: int = 0):
        import hackrf

        self.sdr = hackrf.HackRF()
        self._sample_rate = 2.4e6
        self._center_freq = 100e6
        logger.info(f"Initialized HackRF device {device_index}")

    def set_sample_rate(self, rate: float) -> None:
        self._sample_rate = rate
        self.sdr.sample_rate = rate

    def set_center_frequency(self, freq: float) -> None:
        self._center_freq = freq
        self.sdr.center_freq = freq

    def set_gain(self, gain: str | float) -> None:
        if isinstance(gain, str) and gain == "auto":
            gain = 20  # Default gain
        self.sdr.lna_gain = int(gain)

    def read_samples(self, num_samples: int) -> np.ndarray:
        return self.sdr.read_samples(num_samples)

    def close(self) -> None:
        self.sdr.close()
