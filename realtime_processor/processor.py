import numpy as np
import re
import os
import datetime
from realtime_processor.singlestationutil import get_station_type, rcus_in_station, make_xst_plots

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
    xcsubband = None

    with open(shell_script, "r") as file:
        lines = file.readlines()

    # First, look for an uncommented --xcsubband= line
    for line in lines:
        # Ignore lines that start with '#' (commented out)
        if not line.strip().startswith("#"):
            match_a = re.search(r"--xcsubband\s*=\s*(\d+)", line)
            if match_a:
                print(f"Subband: {match_a.group(1)}")
                return int(match_a.group(1)), int(match_a.group(1))

    # If not found, look for subbands=['150:271'] (even in commented lines)
    for line in lines:
        match_b = re.search(r"subbands=['\"]?(\d+):(\d+)['\"]?", line)
        if match_b:
            first_number = int(match_b.group(1))
            second_number = int(match_b.group(2))
            print(f"Subband range: {first_number} to {second_number}")
            return first_number, second_number

    # If nothing found
    print("No subband information found.")
    return None, None

def get_rcu_mode(shell_script):
    """Extract RCU mode from a shell script (.sh)."""
    try:
        with open(shell_script, "r") as file:
            for line in file:
                match = re.search(r"rcumode=(\d)", line)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Error reading {shell_script}: {e}")
    return None