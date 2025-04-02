import numpy as np
import re
import os
import datetime
from lofarimaging.singlestationutil import get_station_type, rcus_in_station, make_xst_plots

def process_data(covariance_matrix, subband, dat_path, output_dir, station_name="LV614", rcu_mode="3"):
    obstime = get_obstime(dat_path)
    make_xst_plots(covariance_matrix, station_name, obstime, subband, rcu_mode, outputpath=output_dir, sky_only=True)

def get_obstime(dat_path):
    obsdatestr, obstimestr, *_ = os.path.basename(dat_path).rstrip(".dat").split("_")
    obstime = datetime.datetime.strptime(obsdatestr + ":" + obstimestr, '%Y%m%d:%H%M%S')
    return obstime

def get_subband(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    match = re.search(r'--xcsubband=(\d+)', content)
    if match:
        subband = int(match.group(1))
    else:
        subband = None 

    return subband

def get_subband_from_shell(shell_script):
    """Extract subband from a shell script (.sh)."""
    try:
        with open(shell_script, "r") as file:
            for line in file:
                # Case A: rspctl --xcsubband=167
                match_a = re.search(r"rspctl\s+--xcsubband=(\d+)", line)
                if match_a:
                    return int(match_a.group(1))

                # Case B: subbands='150:271' (return first number)
                match_b = re.search(r"subbands=['\"](\d+):\d+['\"]", line)
                if match_b:
                    return int(match_b.group(1))

    except Exception as e:
        print(f"Error reading {shell_script}: {e}")
    return None

def obs_parser(obs_file):
    obs_data = {'beams': []}
    with open(obs_file) as obs:
        lines = obs.readlines()
        for line in lines:
            if line.startswith('bits='):
                obs_data['bits'] = line.split('=')[1].replace('\n', '')

            elif line.startswith('rspctl --bitmode'):
                obs_data['bits'] = line.split('=')[1].replace('\n', '')

            elif line.startswith('- rspctl --bitmode'):
                obs_data['bits'] = line.split('=')[1].replace('\n', '')

            elif line.startswith('subbands='):
                obs_data['subbands'] = line.split('=')[1].replace('\n', '').replace("'", "")

            elif line.startswith("nohup beamctl "):
                beam_data = line.split()
                obs_data['beams'].append({'name': beam_data[7].split("=")[1].replace('$', '').lstrip('0,0,'),
                                          'beamlets': beam_data[6].split("=")[1]})

            elif line.startswith("$PREFIX beamctl"):
                beam_data = line.split()
                obs_data['beams'].append({'name': beam_data[7].split("=")[1].replace('$', '').lstrip('0,0,'),
                                          'beamlets': beam_data[6].split("=")[1]})

            elif line.startswith("- beamctl "):
                line = line.replace("- ", "")
                beam_data = line.split()
                source_name = get_source_name(beam_data[7].split("=")[1].replace('$', ''))
                obs_data['beams'].append({'name': source_name, 'beamlets': beam_data[4].split("=")[1]})
    return obs_data