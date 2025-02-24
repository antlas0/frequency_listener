#!/usr/bin/env python


import logging

from .configuration import ExporterConfiguration

from .lf_thread import LFThread

logger = logging.getLogger(__name__)

class Exporter(LFThread):
    """Manage data"""
    def __init__(self, configuration:ExporterConfiguration):
        super().__init__()
        self._configuration = configuration
    
    def setup(self) -> bool:
        logger.info("Exporter set up.")
        return True

    def quit(self) -> bool:
        return True