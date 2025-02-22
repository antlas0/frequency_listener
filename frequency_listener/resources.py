#!/usr/bin/env python

from enum import Enum
from dataclasses import dataclass
import numpy as np

class DemodulationType(Enum):
    UNKNOWN=0
    FM=1
    AM=2

class BandwidthSize(Enum):
    UNKNOWN=0
    WIDE=25000
    NARROW=12500
    BROADCAST=200000

@dataclass
class SignalMetadata:
    frequency: int
    bandwidth: BandwidthSize

@dataclass
class SignalStruct:
    samples: np.array
    sample_rate: int
    timestamp: float
    metadata: SignalMetadata

@dataclass
class AudioMetadata:
    title: str

@dataclass
class AudioStruct:
    audio: np.array
    rate: int
    metadata: AudioMetadata
