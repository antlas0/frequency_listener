# frequency_listener
This tool is able to record IQs and perform FM demodulation and save the resulting audio to disk. IQ data is saved as Python `pickle` data, Audio is saved as Waveform Audio File Format `.wav`.


> [!IMPORTANT]  
> Please refer to your juridiction to know if you are allowed to record, save and potentially share IQ or demodulated data.

## Details
This small tool emerges from different needs:
* Dive into IQ and demodulation
* Record my RF tests
* Detect RF activity and be notified about it


## Prerequisites
An [RTLSDR](https://en.wikipedia.org/wiki/List_of_software-defined_radios) USB dongle.

## How to use
#### Configuration

Edit the configuration file `frequency_listener.ini` accordingly.
```ini
[listener]
duration_s=15 # How long we want to listen

[device_configuration]
center_frequency=105100000 # On which frequency we want to listen
sample_rate=1200000 # Sample rate
frequency_correction_ppm=1 # frequency offset in ppm -- unique for each device

[fm_demodulator_configuration]
enable=true
snr_db=5 # Filter sample by SNR. If computed SNR is under this threshold, sample is discarded and not demodulated
bandwidth=wide # Wide or Narrow band demodulation
max_chunk_size_b=3500000 # If size in bytes is reached, export
max_delay_s=300 # If samples are accumulated until this time window, export
has_ctcss=false # If ctcss should be removed

[exporter_configuration]
enable=true
output_directory=output # Directory to export audio files
```
#### How to install

There are many ways to set up an Python environment, here is a suggestion:
```bash
$ python -m venv .venv
$ source ./venv/bin/activate
$ python -m pip install -r requirements.txt
```

#### How to launch

In the root directoy of the project, call the tool as a python module, passing the configuration file path.

```bash
$ python -m frequency_listener -c frequency_listener.ini
```
