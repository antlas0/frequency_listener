#!/usr/bin/env python

import os
import logging
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from .configuration import DeviceConfiguration
from .resources import SignalStruct, SignalMetadata
from .device import Device

logger = logging.getLogger(__name__)

class VirtualDevice(Device):
    """SDR device manager"""
    def __init__(self, configuration:DeviceConfiguration):
        super().__init__(configuration)

    def setup(self) -> bool:
        """Setup the device"""
        logger.info("Setup virtual device")
        return True

    def quit(self) -> bool:
        """Teardown"""
        logger.info("Closing virtual device")
        return True

    def run(self) -> None:
        logger.info(f"Reading IQ files from {self._configuration.iq.output_dir}")

        collected_files:list = sorted(Path(self._configuration.iq.output_dir).iterdir(), key=os.path.getmtime)

        for collected_file in collected_files:
            if not os.path.isfile(collected_file):
                continue
            with open(collected_file, 'rb') as f:
                logger.info(f"Loading {collected_file}")
                x = pickle.load(f)
                data = SignalStruct(
                    samples=x,
                    sample_rate=self._configuration.sample_rate,
                    timestamp=datetime.now().timestamp(),
                    metadata=SignalMetadata(
                        frequency=self._configuration.center_frequency,
                        bandwidth=self._configuration.bandwidth
                    )
                )
                self.publish(data)
