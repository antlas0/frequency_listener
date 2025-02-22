#!/usr/bin/env python


from .listener import Listener
from .resources import BandwidthSize
from .configuration import *


import logging
import argparse
import configparser
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Frequecny listener")
    argparser.add_argument("-c", "--configuration-file", help="Path to configuration file, default frequency_listener.ini", action="store", default="frequency_listener.ini")
    args = argparser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.configuration_file)

    lc = ListenerConfiguration(
        duration_s=float(config["listener"].get("duration_s", 30)),
        export=bool(config["exporter_configuration"]["enable"].lower() == "true")
    )

    bd = DemodulationType.FM
    bw = BandwidthSize.WIDE
    if config["fm_demodulator_configuration"].get("bandwidth", "wide") == "narrow":
        bw = BandwidthSize.NARROW
    if config["fm_demodulator_configuration"].get("bandwidth", "wide") == "broadcast":
        bw = BandwidthSize.BROADCAST
  
    iqc = IQConfiguration()
    if config["iq"].get("enable", "false") == "true":
        iqc.record = True
        iqc.output_dir= config["iq"].get("output_dir", "output")

    dc = DeviceConfiguration(
        center_frequency=int(config["device_configuration"].get("center_frequency")),
        sample_rate=int(config["device_configuration"].get("sample_rate", 1200000)),
        frequency_correction_ppm=float(config["device_configuration"].get("frequency_correction_ppm", 1)),
        read_chunk_size=int(config["device_configuration"].get("read_chunk_size", 2097152)),
        frequency_offset=int(config["device_configuration"].get("frequency_offset", 0)),
        bandwidth=bw,
        iq=iqc,
    )

    max_delay_s:int = int(config["fm_demodulator_configuration"].get("max_delay_s", 30))
    if max_delay_s > lc.duration_s:
        max_delay_s = lc.duration_s
    fc = FMDemodulatorConfiguration(
        snr_db=float(config["fm_demodulator_configuration"].get("snr_db", 0)),
        demodulation_type=bd,
        max_delay_s=max_delay_s,
        max_chunk_size_b=int(config["fm_demodulator_configuration"].get("max_chunk_size_b", 50000)),
        has_ctcss=bool(config["fm_demodulator_configuration"].get("has_ctcss", "false").lower()=="true"),
    )

    sc = FileExporterConfiguration(
        output_directory=config["exporter_configuration"].get("output_directory", "output")
    )

    listener = Listener(
        device_params=dc,
        demodulator_params=fc,
        exporter_params=sc,
        configuration=lc
    )
    if listener.setup():
        listener.run()
