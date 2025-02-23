#!/usr/bin/env python

import logging
from .configuration import DeviceConfiguration

from .lf_thread import LFThread

logger = logging.getLogger(__name__)

class Device(LFThread):
    """SDR device manager"""
    def __init__(self, configuration:DeviceConfiguration):
        super().__init__()
        self._configuration:DeviceConfiguration = configuration

    def setup(self) -> bool:
        """Setup the device"""
        return True

    def quit(self) -> bool:
        """Teardown"""
        return True

    def run(self) -> None:
        pass