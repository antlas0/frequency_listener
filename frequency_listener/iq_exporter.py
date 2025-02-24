#!/usr/bin/env python

import os
import queue
import pickle
import logging
from datetime import datetime

from .exporter import Exporter
from .configuration import ExporterConfiguration
from .resources import SignalStruct

logger = logging.getLogger(__name__)

class IQExporter(Exporter):
    """Manage data"""
    def __init__(self, configuration:ExporterConfiguration) -> None:
        super(IQExporter, self).__init__(configuration)
        self._max_queue_timeout_s = 1

    def setup(self) -> bool:
        if not os.path.isdir(self._configuration.output_directory):
            os.mkdir(self._configuration.output_directory)
        return True

    def run(self) -> None:
        logger.info(f"Running IQ exporter")
        while self._running:
            try:
                data = self._input_queue.get(
                    block=self._running,
                    timeout=self._max_queue_timeout_s,
                )
            except queue.Empty:
                pass
            else:
                self.iq_save(data)
            finally:
                pass

    def quit(self) -> bool:
        logger.info("Closing IQ exporter")
        return self.teardown()

    def iq_save(self, data:SignalStruct) -> bool:
        res:bool = False
        date = datetime.fromtimestamp(data.timestamp).strftime("%Y-%m-%d__%H_%M_%S")
        filepath: str = os.path.join(
                self._configuration.output_directory,
                f"iq_{data.metadata.frequency}_{data.sample_rate}_{date}.pkl"
            )
        try:
            with open(filepath, "wb") as file:
                pickle.dump(data.samples, file=file)
        except Exception as e:
            logger.error(f"Could not save IQ samples: {e}")
        else:
            logger.info(f"Exported IQs to file {filepath}")
            res = True
        return res
