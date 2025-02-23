#!/usr/bin/env python

import logging

import threading
from queue import Queue
from .configuration import DeviceConfiguration, DemodulatorConfiguration, ListenerConfiguration, ExporterConfiguration
from .resources import DemodulationType
from .fm_demodulator import FMDemodulator
from .demodulator import Demodulator
from .file_exporter import FileExporter
from .device import Device
from .sdr_device import SDRDevice
from .virtual_device import VirtualDevice

logger = logging.getLogger(__name__)

class Listener(threading.Thread):
    """Frequency listener"""
    def __init__(self, \
                    device_params:DeviceConfiguration, \
                    demodulator_params:DemodulatorConfiguration, \
                    exporter_params: ExporterConfiguration, \
                    configuration:ListenerConfiguration):
        self._configuration:ListenerConfiguration = configuration
        self._demodulator_params:DemodulatorConfiguration = demodulator_params
        self._device:Device = None
        self._device_params:DeviceConfiguration = device_params
        self._exporter = None
        self._demodulator:Demodulator = None
        self._exporter_params = exporter_params
        self._signal_queue:Queue = Queue(maxsize=512)
        self._audio_queue:Queue = Queue(maxsize=512)
        self._timer:threading.Timer = None

    def setup(self) -> bool:
        if self._device_params.virtual:
            self._device = VirtualDevice(self._device_params)
        else:
            self._device = SDRDevice(self._device_params)
        self._device.set_output_queue(self._signal_queue)

        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator:Demodulator = FMDemodulator(self._demodulator_params)
            self._demodulator.set_input_queue(self._signal_queue)
            self._demodulator.set_output_queue(self._audio_queue)

        if self._configuration.export is True:
            self._exporter = FileExporter(self._exporter_params)
            self._exporter.set_input_queue(self._audio_queue)

        self._timer = threading.Timer(self._configuration.duration_s, self.teardown)
        logger.info(f"Listening during {self._configuration.duration_s} seconds.")

        self._device.setup()

        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator.setup()

        if self._configuration.export is True:
            self._exporter.setup()

        return True

    def teardown(self) -> bool:
        self._device.quit()
        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator.quit()
        if self._configuration.export is True:
            self._exporter.quit()
        return True

    def run(self) -> None:
        self._device.start()
        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator.start()
        if self._configuration.export is True:
            self._exporter.start()
        self._timer.start()

        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator.join()
        if self._configuration.export is True:
            self._exporter.join()
        self._device.join()
