#!/usr/bin/env python

import numpy as np
import scipy.signal as signal
import logging
from sys import getsizeof
from datetime import datetime, timedelta
import queue
from typing import Union

from .configuration import FMDemodulatorConfiguration
from .resources import SignalMetadata, AudioStruct, AudioMetadata, BandwidthSize
from .demodulator import Demodulator


logger = logging.getLogger(__name__)

class FMDemodulator(Demodulator):
    """FM demodulator"""
    def __init__(self, configuration: FMDemodulatorConfiguration):
        super().__init__(configuration)
        self._configuration = configuration
        self._audio_rate = 44100
        self._recorded_audio = []
        self._start_chunk_time = datetime.now()
        self._max_queue_timeout_s = 1
    
    def setup(self) -> bool:
        logger.info("FM demodulator set up.")
        return True

    def _remove_ctcss(self, x:np.array, sample_rate:int) -> np.array:
        # Low-pass filter below 300 Hz to extract CTCSS
        b_ctcss, a_ctcss = signal.butter(4, 300 / (sample_rate / 2), btype='low')
        # ctcss_tone = signal.filtfilt(b_ctcss, a_ctcss, x4)

        # High-pass filter above 300 Hz to remove CTCSS from voice
        b_voice, a_voice = signal.butter(4, 300 / (sample_rate / 2), btype='high')
        y = signal.filtfilt(b_voice, a_voice, x)
        return y

    def _lowpass_filter(self, x:np.array, cutoff:int, fs:int, order:int=5):
            nyquist = 0.5 * fs  
            normal_cutoff = cutoff / nyquist  
            b, a = signal.butter(order, normal_cutoff, btype="lowpass", analog=True)
            return signal.lfilter(b, a, x)

    def demodulate_fm_broadcast(self, x1: np.array, sample_rate: int):
        """
        Demodulate FM (WFM) with proper filtering, decimation, and de-emphasis.
        """
        # Select appropriate bandwidth for mode
        tau:float = 75e-6  # De-emphasis time constant (75µs for US, 50µs for EU)
        audio_gain:int = 1000

        # Compute Decimation Rate
        dec_rate = int(sample_rate / (BandwidthSize.BROADCAST.value * 2))
        new_fs:int = int(BandwidthSize.BROADCAST.value * 2)
    
        x3 = signal.decimate(x1, dec_rate, zero_phase=True)

        ### FM Demodulation (Polar Discriminator)
        y4 = x3[1:] * np.conj(x3[:-1])
        x4 = np.angle(y4)

        d = new_fs * tau  # -3dB point for de-emphasis
        x = np.exp(-1/d)
        b = [1 - x]
        a = [1, -x]
        x5 = signal.lfilter(b, a, x4)

        # Find a suitable decimation rate to get an audio rate of ~44-48 kHz
        dec_audio = int(new_fs / self._audio_rate)
        x6 = signal.decimate(x5, dec_audio, zero_phase=True)

        # Scale audio for volume adjustment
        x6 *= audio_gain / np.max(np.abs(x6))
        return x6

    def demodulate_fm_wide(self, x1: np.array, sample_rate: int):
        """
        Demodulate FM (WFM) with proper filtering, decimation, and de-emphasis.
        """
        # Compute Decimation Rate
        dec_rate = int(4)
        new_fs:int = int(sample_rate/4)
    
        x3 = signal.decimate(x1, dec_rate, zero_phase=True)

        ### FM Demodulation (Polar Discriminator)
        y4 = x3[1:] * np.conj(x3[:-1])
        x4 = np.angle(y4)

        if self._configuration.has_ctcss:
            x4 = self._remove_ctcss(x4, new_fs)

        tau:float = 75e-6  # De-emphasis time constant (75µs for US, 50µs for EU)
        d = new_fs * tau  # -3dB point for de-emphasis
        x = np.exp(-1/d)
        b = [1 - x]
        a = [1, -x]
        x5 = signal.lfilter(b, a, x4)

        # Find a suitable decimation rate to get an audio rate of ~44-48 kHz
        dec_audio = int(new_fs / self._audio_rate)
        x6 = signal.decimate(x5, dec_audio, zero_phase=True)

        # Scale audio for volume adjustment
        audio_gain:int = 1000
        x6 *= audio_gain / np.max(np.abs(x6))
        return x6

    def demodulate_fm_narrow(self, x1: np.array, sample_rate: int):
        """
        Demodulate FM (NBFM) with proper filtering, decimation.
        """
        audio_gain:int = 10000

        dec_rate = int(5)
        new_fs:int = int(sample_rate/dec_rate)
        x3 = signal.decimate(x1, dec_rate, zero_phase=True)

        ### FM Demodulation (Polar Discriminator)
        y4 = x3[1:] * np.conj(x3[:-1])
        x4 = np.angle(y4)

        if self._configuration.has_ctcss:
            x4 = self._remove_ctcss(x4, new_fs)

        # Find a suitable decimation rate to get an audio rate of ~44-48 kHz
        dec_audio = int(new_fs / self._audio_rate)
        x5 = signal.decimate(x4, dec_audio, zero_phase=True)

        # Scale audio for volume adjustment
        x5 *= audio_gain / np.max(np.abs(x5))
        return x5

    def time_window_has_passed(self, timestamp:int) -> bool:
        return datetime.fromtimestamp(timestamp) - self._start_chunk_time > timedelta(seconds=self._configuration.max_delay_s)

    def demodulate(self, iq_samples:np.array, sample_rate:int, bandwidth:BandwidthSize) -> None:
        demodulators = {
            BandwidthSize.NARROW.name: self.demodulate_fm_narrow,
            BandwidthSize.WIDE.name: self.demodulate_fm_wide,
            BandwidthSize.BROADCAST.name: self.demodulate_fm_broadcast,
        }
        return demodulators[bandwidth.name](iq_samples, sample_rate)

    def process_data(self, iq_samples:np.array, sample_rate:int, timestamp:int, metadata:SignalMetadata) -> None:
        snr_db: float = self.compute_snr(iq_samples, sample_rate, metadata.bandwidth)
        if not self.snr_threshold(snr_db):
            logger.warning(f"SNR not enough {snr_db} dB vs {self._configuration.snr_db} dB")
            return

        audio_signal = self.demodulate(iq_samples, sample_rate, metadata.bandwidth)

        self._recorded_audio.extend(audio_signal)

        logger.info(f"Sample size {getsizeof(self._recorded_audio)} bytes.")

        if len(self._recorded_audio) > 0 and \
            (getsizeof(self._recorded_audio) > self._configuration.max_chunk_size_b or self.time_window_has_passed(timestamp)):
            self._recorded_audio = self._recorded_audio / np.max(np.abs(self._recorded_audio)) * 0.9  # Scale to avoid clipping
            self.publish(
                AudioStruct(
                    audio=self._recorded_audio,
                    rate=int(self._audio_rate),
                    metadata=AudioMetadata(
                        title=f"{metadata.frequency}_{metadata.bandwidth.name.lower()}"
                    ),
                )
            )
            self._recorded_audio = []
            self._start_chunk_time = datetime.now()

    def run(self) -> None:
        logger.info(f"Running FM demodulator with configuration {self._configuration}")
        while self._running:
            try:
                data = self._input_queue.get(
                    block=self._running,
                    timeout=self._max_queue_timeout_s,
                )
            except queue.Empty:
                pass
            else:
                self.process_data(data.samples, data.sample_rate, data.timestamp, data.metadata)
            finally:
                pass

    def quit(self) -> bool:
        logger.info("Closing fm demodulator")
        return self.teardown()

