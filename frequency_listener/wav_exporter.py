#!/usr/bin/env python

import os
import queue
import logging
import numpy as np
import soundfile as sf
from datetime import datetime

from .exporter import Exporter
from .configuration import ExporterConfiguration

logger = logging.getLogger(__name__)

class WavExporter(Exporter):
    """Manage data"""
    def __init__(self, configuration:ExporterConfiguration) -> None:
        super(WavExporter, self).__init__(configuration)
        self._max_queue_timeout_s = 1

    def setup(self) -> bool:
        if not os.path.isdir(self._configuration.output_directory):
            os.mkdir(self._configuration.output_directory)
        return True

    def write(self, content:np.array, rate:int, title:str) -> bool:
        date = datetime.now().strftime("%Y-%m-%d__%H_%M_%S")
        filepath: str = f"audio_{title}_{date}.wav"
        logger.info(f"Exporting audio to file {filepath}")
        sf.write(os.path.join(self._configuration.output_directory, filepath), content, rate)

    def run(self) -> None:
        logger.info(f"Running Exporter")
        while self._running:
            try:
                samples = self._input_queue.get(
                    block=self._running,
                    timeout=self._max_queue_timeout_s,
                )
            except queue.Empty:
                pass
            else:
                self.write(samples.audio, samples.rate, samples.metadata.title)
            finally:
                pass

    def quit(self) -> bool:
        logger.info("Closing file exporter")
        return self.teardown()
