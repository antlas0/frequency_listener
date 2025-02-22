#!/usr/bin/env python


import logging
from typing import List, Any
from threading import Thread
from queue import Queue

from .configuration import ExporterConfiguration

logger = logging.getLogger(__name__)

class LFThread(Thread):
    """Manage data"""
    def __init__(self):
        super().__init__()
        self._input_queue:Queue = None
        self._output_queues:List[Queue] = []
        self._running = True

    def set_input_queue(self, q:Queue):
        self._input_queue = q

    def set_output_queue(self, q:Queue):
        self._output_queues.append(q)

    def clear_input_queue(self) -> None:
        if self._input_queue is None:
            return
        while not self._input_queue.empty():
            try:
                self._input_queue.get(block=False)
            except Exception as e:
                logger.warning(str(e))
                continue
            self._input_queue.task_done()

    def publish(self, data:Any):
        for q in self._output_queues:
            q.put(data)

    def teardown(self) -> bool:
        self.clear_input_queue()
        self._running = False
        return True

    def run(self) -> None:
        while self._running:
            samples = self._input_queue.get()
            self.demodulate(samples)

    def demodulate(self) -> None:
        pass
