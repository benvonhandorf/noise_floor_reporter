"""Base protocol for SDR backends."""

from typing import Protocol
import numpy as np


class SDRBackend(Protocol):
    """Protocol defining the interface for SDR backends."""

    def set_sample_rate(self, rate: float) -> None:
        """Set the sample rate."""
        ...

    def set_center_frequency(self, freq: float) -> None:
        """Set the center frequency."""
        ...

    def set_gain(self, gain: str | float) -> None:
        """Set the gain."""
        ...

    def read_samples(self, num_samples: int) -> np.ndarray:
        """Read samples from the SDR."""
        ...

    def close(self) -> None:
        """Close the SDR device."""
        ...
