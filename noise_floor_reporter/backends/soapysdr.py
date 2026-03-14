"""SoapySDR backend implementation with network protocol support."""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class SoapySDRBackend:
    """SoapySDR backend implementation with network protocol support."""

    def __init__(self, device_index: int = 0, device_args: Optional[str] = None):
        """Initialize SoapySDR backend.

        Args:
            device_index: Device index (used if device_args not specified)
            device_args: SoapySDR device arguments string (e.g., "driver=remote,remote=192.168.1.100")
        """
        try:
            import SoapySDR

            self.SoapySDR = SoapySDR

            # Parse device arguments
            if device_args:
                # Parse device string into dict
                args_dict = {}
                for arg in device_args.split(","):
                    if "=" in arg:
                        key, value = arg.split("=", 1)
                        args_dict[key.strip()] = value.strip()
                logger.info(f"Initializing SoapySDR with args: {args_dict}")
                self.sdr = SoapySDR.Device(args_dict)
            else:
                # Use device index
                devices = SoapySDR.Device.enumerate()
                if device_index >= len(devices):
                    raise ValueError(
                        f"Device index {device_index} out of range. "
                        f"Found {len(devices)} devices."
                    )
                logger.info(f"Initializing SoapySDR device {device_index}")
                self.sdr = SoapySDR.Device(devices[device_index])

            # Setup RX stream
            self.stream = self.sdr.setupStream(SoapySDR.SOAPY_SDR_RX, SoapySDR.SOAPY_SDR_CF32)
            self._sample_rate = 2.4e6
            self._gain_mode = "auto"

            logger.info(
                f"Initialized SoapySDR: {self.sdr.getHardwareKey()} "
                f"({self.sdr.getDriverKey()})"
            )

        except ImportError:
            raise ImportError("SoapySDR library not available. Install with: pip install SoapySDR")
        except Exception as e:
            logger.error(f"Failed to initialize SoapySDR: {e}")
            raise

    def set_sample_rate(self, rate: float) -> None:
        """Set sample rate."""
        self._sample_rate = rate
        self.sdr.setSampleRate(self.SoapySDR.SOAPY_SDR_RX, 0, rate)
        actual_rate = self.sdr.getSampleRate(self.SoapySDR.SOAPY_SDR_RX, 0)
        logger.debug(f"Set sample rate to {actual_rate} Hz (requested {rate} Hz)")

    def set_center_frequency(self, freq: float) -> None:
        """Set center frequency."""
        self.sdr.setFrequency(self.SoapySDR.SOAPY_SDR_RX, 0, freq)
        actual_freq = self.sdr.getFrequency(self.SoapySDR.SOAPY_SDR_RX, 0)
        logger.debug(f"Set frequency to {actual_freq} Hz (requested {freq} Hz)")

    def set_gain(self, gain: str | float) -> None:
        """Set gain."""
        self._gain_mode = gain

        if isinstance(gain, str) and gain == "auto":
            # Enable automatic gain control if available
            if self.sdr.hasGainMode(self.SoapySDR.SOAPY_SDR_RX, 0):
                self.sdr.setGainMode(self.SoapySDR.SOAPY_SDR_RX, 0, True)
                logger.debug("Enabled automatic gain control")
            else:
                # Set to a reasonable default if AGC not available
                self.sdr.setGain(self.SoapySDR.SOAPY_SDR_RX, 0, 30.0)
                logger.debug("AGC not available, set gain to 30 dB")
        else:
            # Manual gain setting
            if self.sdr.hasGainMode(self.SoapySDR.SOAPY_SDR_RX, 0):
                self.sdr.setGainMode(self.SoapySDR.SOAPY_SDR_RX, 0, False)
            self.sdr.setGain(self.SoapySDR.SOAPY_SDR_RX, 0, float(gain))
            actual_gain = self.sdr.getGain(self.SoapySDR.SOAPY_SDR_RX, 0)
            logger.debug(f"Set gain to {actual_gain} dB (requested {gain} dB)")

    def read_samples(self, num_samples: int) -> np.ndarray:
        """Read samples from the SDR."""
        # Activate stream
        self.sdr.activateStream(self.stream)

        # Allocate buffer for complex float32 samples
        buff = np.empty(num_samples, dtype=np.complex64)

        # Read samples
        samples_read = 0
        while samples_read < num_samples:
            sr = self.sdr.readStream(self.stream, [buff[samples_read:]], num_samples - samples_read)
            if sr.ret > 0:
                samples_read += sr.ret
            else:
                logger.warning(f"Stream read returned {sr.ret}")
                break

        # Deactivate stream
        self.sdr.deactivateStream(self.stream)

        logger.debug(f"Read {samples_read} samples")
        return buff[:samples_read]

    def close(self) -> None:
        """Close the SDR device."""
        try:
            if hasattr(self, "stream"):
                self.sdr.closeStream(self.stream)
            if hasattr(self, "sdr"):
                self.sdr = None
            logger.info("Closed SoapySDR device")
        except Exception as e:
            logger.error(f"Error closing SoapySDR device: {e}")
