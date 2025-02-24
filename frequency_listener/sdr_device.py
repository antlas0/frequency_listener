#!/usr/bin/env python

import os
import logging
import rtlsdr
import numpy as np
from typing import Optional
from datetime import datetime
from .configuration import DeviceConfiguration
from .resources import SignalStruct, SignalMetadata
from .device import Device

logger = logging.getLogger(__name__)

class SDRDevice(Device):
    """SDR device manager"""
    def __init__(self, configuration:DeviceConfiguration):
        super().__init__(configuration)
        self.sdr:Optional[rtlsdr.rtlsdraio.RtlSdrAio] = None

    def setup(self) -> bool:
        """Setup the device"""
        res: bool = False
        try:
            self.sdr = rtlsdr.RtlSdr(self._configuration.device_index)
        except Exception as e:
            logger.error("Could not set up device.")
            logger.error(f"{e}")
            self._running = False
        else:
            logger.info("Device successfully set up.")
            logger.info(f"Configuring device with: {self._configuration}")
            res = True
            self.sdr.sample_rate = self._configuration.sample_rate
            self.sdr.center_freq = self._configuration.center_frequency+self._configuration.frequency_offset
            self.sdr.gain = self._configuration.gain
            self.sdr.bandwidth = int(self._configuration.bandwidth.value)
            if self._configuration.frequency_correction_ppm > 0:
                self.sdr.freq_correction = int(self._configuration.center_frequency * self._configuration.frequency_correction_ppm /1e6)
            logger.info(f"{self.sdr}")

        finally:
            pass
        return res

    def quit(self) -> bool:
        """Teardown"""
        logger.info("Closing SDR device")
        return self.teardown()

    def run(self) -> None:
        logger.info(f"Running SDR device")

        while self._running:
            iq_samples = self.sdr.read_samples(self._configuration.read_chunk_size)
            samples = np.array(iq_samples).astype("complex64")
            data = SignalStruct(
                samples=samples,
                sample_rate=self.sdr.sample_rate,
                timestamp=datetime.now().timestamp(),
                metadata=SignalMetadata(
                    frequency=self._configuration.center_frequency,
                    bandwidth=self._configuration.bandwidth
                )
            )
            self.publish(data)
