#!/usr/bin/env python

import logging

import threading
from queue import Queue
from .configuration import DeviceConfiguration, DemodulatorConfiguration, ListenerConfiguration, ExporterConfiguration, FileExporterConfiguration
from .resources import DemodulationType
from .fm_demodulator import FMDemodulator
from .demodulator import Demodulator
from .wav_exporter import WavExporter
from .iq_exporter import IQExporter
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
        self._device_queue:Queue = Queue(maxsize=512)
        self._iq_queue:Queue = Queue(maxsize=512)
        self._audio_queue:Queue = Queue(maxsize=512)
        self._timer:threading.Timer = None
        self._iq_recorder:IQExporter = None

    def setup(self) -> bool:
        if self._device_params.virtual:
            self._device = VirtualDevice(self._device_params)
        else:
            self._device = SDRDevice(self._device_params)
        self._device.set_output_queue(self._device_queue)
        if self._device_params.iq.record:
            self._iq_recorder = IQExporter(FileExporterConfiguration(output_directory=self._device_params.iq.output_dir))
            self._device.set_output_queue(self._iq_queue)
            self._iq_recorder.set_input_queue(self._iq_queue)

        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator:Demodulator = FMDemodulator(self._demodulator_params)
            self._demodulator.set_input_queue(self._device_queue)
            self._demodulator.set_output_queue(self._audio_queue)

        if self._configuration.export is True:
            self._exporter = WavExporter(self._exporter_params)
            self._exporter.set_input_queue(self._audio_queue)

        self._timer = threading.Timer(self._configuration.duration_s, self.teardown)
        logger.info(f"Listening during {self._configuration.duration_s} seconds.")

        self._device.setup()
        if self._iq_recorder is not None:
            self._iq_recorder.setup()

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
        if self._iq_recorder is not None:
            self._iq_recorder.quit()
        return True

    def run(self) -> None:
        self._device.start()
        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator.start()
        if self._configuration.export is True:
            self._exporter.start()
        if self._iq_recorder is not None:
            self._iq_recorder.start()
        self._timer.start()

        if self._demodulator_params.demodulation_type == DemodulationType.FM:
            self._demodulator.join()
        if self._configuration.export is True:
            self._exporter.join()
        if self._iq_recorder is not None:
            self._iq_recorder.join()
        self._device.join()
