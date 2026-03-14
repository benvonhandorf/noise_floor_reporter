"""SDRPlay backend implementation."""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class SDRPlayBackend:
    """SDRPlay backend implementation."""

    def __init__(self, device_index: int = 0):
        try:
            import sdrplay

            self.sdr = sdrplay.SDRPlay()
            logger.info(f"Initialized SDRPlay device {device_index}")
        except ImportError:
            raise ImportError("SDRPlay library not available")

    def set_sample_rate(self, rate: float) -> None:
        self.sdr.sample_rate = rate

    def set_center_frequency(self, freq: float) -> None:
        self.sdr.center_freq = freq

    def set_gain(self, gain: str | float) -> None:
        if isinstance(gain, str) and gain == "auto":
            self.sdr.agc_enabled = True
        else:
            self.sdr.agc_enabled = False
            self.sdr.if_gain = int(gain)

    def read_samples(self, num_samples: int) -> np.ndarray:
        return self.sdr.read_samples(num_samples)

    def close(self) -> None:
        self.sdr.close()
