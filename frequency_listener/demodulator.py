#!/usr/bin/env python

import logging
import numpy as np
import scipy.signal as signal

from .lf_thread import LFThread
from .configuration import DemodulatorConfiguration
from .resources import BandwidthSize

logger = logging.getLogger(__name__)

class Demodulator(LFThread):
    """FM demodulator"""
    def __init__(self, configuration: DemodulatorConfiguration):
        super().__init__()
        self._configuration = configuration

    def setup(self) -> bool:
        pass

    def quit(self) -> bool:
        logger.info("Closing demodulator")
        return self.teardown()

    def snr_threshold(self, snr_db:float) -> bool:
        """tell if the current sample can be discarded or not"""
        return round(np.max(snr_db), 2) >= round(self._configuration.snr_db, 2)

    def compute_snr(self, iq_data:np.array, sample_rate:int, bandwidth:BandwidthSize) -> float:
        """Compute SNR in dB"""
        # Compute Welch’s Power Spectral Density (PSD)
        freqs, psd = signal.welch(iq_data, fs=sample_rate, nperseg=2048, return_onesided=False, window='hann')

        # Shift frequencies and PSD for correct indexing
        psd = np.fft.fftshift(psd)
        freqs = np.fft.fftshift(freqs)

        # Find the strongest signal peak
        peak_freq_index = np.argmax(psd)
        peak_freq = freqs[peak_freq_index]

        # Define signal region dynamically around detected peak
        half_bw = bandwidth.value / 2
        signal_mask = (freqs > peak_freq - half_bw) & (freqs < peak_freq + half_bw)

        # Define noise region dynamically (avoid exclusion zone around the signal)
        exclusion_half_bw = 25000 / 2
        noise_mask = (freqs < peak_freq - half_bw - exclusion_half_bw) | (freqs > peak_freq + half_bw + exclusion_half_bw)

        # Ensure valid mask sizes
        if np.sum(signal_mask) == 0 or np.sum(noise_mask) == 0:
            raise ValueError("Signal or noise mask is empty. Check bandwidth settings.")

        # Compute power
        signal_power = np.mean(psd[signal_mask])
        noise_power = np.mean(psd[noise_mask])

        # Ensure no negative or zero values
        signal_power = max(signal_power - noise_power, 1e-10)
        snr_db = 10 * np.log10(signal_power / noise_power)

        return snr_db
