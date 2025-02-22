#!/usr/bin/env python

from typing import Union
from dataclasses import dataclass

from .resources import DemodulationType, BandwidthSize

@dataclass
class ExporterConfiguration:
    output_type:str = "file"

@dataclass
class FileExporterConfiguration(ExporterConfiguration):
    output_directory:str = "output"

@dataclass
class IQConfiguration:
    record:bool = False
    output_dir:Union[str, None] = None

@dataclass
class DeviceConfiguration:
    center_frequency: int
    device_index: int=0
    sample_rate: int=2.4e6
    gain : Union[str, int]="auto"
    frequency_correction_ppm: float=20.0
    read_chunk_size: int=4096
    frequency_offset: int=0
    bandwidth: BandwidthSize=BandwidthSize.WIDE
    iq: IQConfiguration = IQConfiguration()

@dataclass
class DemodulatorConfiguration:
    snr_db: float=5.0
    demodulation_type: DemodulationType=DemodulationType.FM

@dataclass
class FMDemodulatorConfiguration(DemodulatorConfiguration):
    max_chunk_size_b: int=350000
    max_delay_s: int=300
    has_ctcss: bool=False

@dataclass
class ListenerConfiguration:
    duration_s: float=10
    export: bool=True
