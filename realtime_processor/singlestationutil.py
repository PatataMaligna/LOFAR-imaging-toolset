# This file was modified by Jorge Cuello (25/03/2025 – 30/05/2025)
# Based on original code from: https://github.com/lofar-astron/lofarimaging
# Licensed under the Apache License, Version 2.0



"""Functions for working with LOFAR single station data"""

import os
import datetime
import configparser
from typing import List, Dict, Tuple, Union

import numpy as np
from packaging import version
import tqdm
import h5py

import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.ticker import FormatStrFormatter
from matplotlib import cm
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.patches import Circle
import matplotlib.axes as maxes
from mpl_toolkits.axes_grid1 import make_axes_locatable

from astropy.coordinates import SkyCoord, GCRS, EarthLocation, AltAz, get_sun, get_body
import astropy.units as u
from astropy.time import Time

from lofarantpos.db import LofarAntennaDatabase
import lofarantpos

from .lofarimaging import sky_imager, skycoord_to_lmn, subtract_sources
from .hdf5util import write_hdf5


__all__ = ["sb_from_freq", "freq_from_sb", "find_caltable", "read_caltable",
           "rcus_in_station", "get_station_pqr", "get_station_xyz", "get_station_type",
            "apply_calibration", "get_full_station_name", "make_sky_movie", "reimage_sky"]

__version__ = "1.5.0"

# Configurations for HBA observations with a single dipole activated per tile.
GENERIC_INT_201512 = [0, 5, 3, 1, 8, 3, 12, 15, 10, 13, 11, 5, 12, 12, 5, 2, 10, 8, 0, 3, 5, 1, 4, 0, 11, 6, 2, 4, 9,
                      14, 15, 3, 7, 5, 13, 15, 5, 6, 5, 12, 15, 7, 1, 1, 14, 9, 4, 9, 3, 9, 3, 13, 7, 14, 7, 14, 2, 8,
                      8, 0, 1, 4, 2, 2, 12, 15, 5, 7, 6, 10, 12, 3, 3, 12, 7, 4, 6, 0, 5, 9, 1, 10, 10, 11, 5, 11, 7, 9,
                      7, 6, 4, 4, 15, 4, 1, 15]
GENERIC_CORE_201512 = [0, 10, 4, 3, 14, 0, 5, 5, 3, 13, 10, 3, 12, 2, 7, 15, 6, 14, 7, 5, 7, 9, 0, 15, 0, 10, 4, 3, 14,
                       0, 5, 5, 3, 13, 10, 3, 12, 2, 7, 15, 6, 14, 7, 5, 7, 9, 0, 15]
GENERIC_REMOTE_201512 = [0, 13, 12, 4, 11, 11, 7, 8, 2, 7, 11, 2, 10, 2, 6, 3, 8, 3, 1, 7, 1, 15, 13, 1, 11, 1, 12, 7,
                         10, 15, 8, 2, 12, 13, 9, 13, 4, 5, 5, 12, 5, 5, 9, 11, 15, 12, 2, 15]

assert version.parse(lofarantpos.__version__) >= version.parse("0.4.0")


def sb_from_freq(freq: float, rcu_mode: Union[int, str] = 1) -> int:
    """
    Convert subband number to central frequency

    Args:
        rcu_mode: rcu mode
        freq: frequency in Hz

    Returns:
        int: subband number

    Example:
        >>> sb_from_freq(58007812.5, '3')
        297
    """
    clock = 200e6
    if int(rcu_mode) == 6:
        clock = 160e6

    freq_offset = 0
    if int(rcu_mode) == 5:
        freq_offset = 100e6
    elif int(rcu_mode) == 6:
        freq_offset = 160e6
    elif int(rcu_mode) == 7:
        freq_offset = 200e6

    sb_bandwidth = 0.5 * clock / 512.
    sb = round((freq - freq_offset) / sb_bandwidth)
    return int(sb)


def freq_from_sb(sb: int, rcu_mode: Union[str, int] = 1):
    """
    Convert central frequency to subband number

    Args:
        rcu_mode: rcu mode
        sb: subband number

    Returns:
        float: frequency in Hz

    Example:
        >>> freq_from_sb(297, '3')
        58007812.5
    """
    clock = 200e6
    freq_offset = 0

    if 'sparse' not in str(rcu_mode):
        if int(rcu_mode) == 6:
            clock = 160e6

        if int(rcu_mode) == 5:
            freq_offset = 100e6
        elif int(rcu_mode) == 6:
            freq_offset = 160e6
        elif int(rcu_mode) == 7:
            freq_offset = 200e6

    sb_bandwidth = 0.5 * clock / 512.
    freq = (sb * sb_bandwidth) + freq_offset
    return freq


def find_caltable(field_name: str, rcu_mode: Union[str, int], caltable_dir='caltables'):
    """
    Find the file of a caltable.

    Args:
        field_name: Name of the antenna field, e.g. 'DE602LBA' or 'DE602'
        rcu_mode: Receiver mode for which the calibration table is requested.
        caltable_dir: Root directory under which station information is stored in
            subdirectories DE602C/etc/, RS106/etc/, ...
    Returns:
        str: full path to caltable if it exists, None if nothing found

    Example:
        >>> find_caltable("DE603LBA", "3", caltable_dir="test/CalTables")
        'test/CalTables/DE603/CalTable-603-LBA_INNER-10_90.dat'

        >>> find_caltable("ES615HBA", "5") is None
        True
    """
    station, field = field_name[0:5].upper(), field_name[5:].upper()
    station_number = station[2:5]

    filename = f"CalTable-{station_number}"

    if str(rcu_mode) in ('outer', '1', '2'):
        filename += "-LBA_OUTER-10_90.dat"
    elif str(rcu_mode) in ('inner', '3', '4'):
        filename += "-LBA_INNER-10_90.dat"
    elif str(rcu_mode) == '5':
        filename += "-HBA-110_190.dat"
    elif str(rcu_mode) == '6':
        filename += "-HBA-170_230.dat"
    elif str(rcu_mode) == '7':
        filename += "-HBA-210_250.dat"
    elif str(rcu_mode) == 'sparse_even':
        filename += "-LBA_SPARSE_EVEN-10_90.dat"
    elif str(rcu_mode) == 'sparse_odd':
        filename += "-LBA_SPARSE_ODD-10_90.dat"
    else:
        raise RuntimeError("Unexpected mode: " + str(rcu_mode) + " for field_name " + str(field_name))

    if os.path.exists(os.path.join(caltable_dir, filename)):
        # All caltables in one directory
        # return os.path.normpath(os.path.join(caltable_dir, filename))
        ###TO pass the test as windows user
        path = os.path.normpath(os.path.join(caltable_dir, filename))
        return path.replace("\\", "/") 
    elif os.path.exists(os.path.join(caltable_dir, station, filename)):
        # Caltables in a directory per station
        # return os.path.normpath(os.path.join(caltable_dir, station, filename))
        ###TO pass the test as windows user
        path = os.path.normpath(os.path.join(caltable_dir, station, filename))
        return path.replace("\\", "/") 
    else:
        return None


def read_caltable(filename: str, num_subbands=512) -> Tuple[Dict[str, str], np.ndarray]:
    """
    Read a station's calibration table.

    Args:
        filename: Filename with the caltable
        num_subbands: Number of subbands

    Returns:
        Tuple[Dict[str, str], np.ndarray]: A tuple containing a dict with
            the header lines, and a 2D numpy.array of complex numbers
            representing the station gain coefficients.
    """
    infile = open(filename, 'rb')

    header_lines = []

    try:
        while True:
            header_lines.append(infile.readline().decode('utf8').strip())
            if 'HeaderStop' in header_lines[-1]:
                break
    except UnicodeDecodeError:
        # No header; close and open again
        infile.close()
        infile = open(filename, 'rb')

    caldata = np.fromfile(infile, dtype=np.complex128)
    num_rcus = len(caldata) // num_subbands

    infile.close()

    header_dict = {key: val for key, val in [line.split(" = ")
                                             for line in header_lines[1:-1]]}

    return header_dict, caldata.reshape((num_subbands, num_rcus))


def apply_calibration(visibilities: np.ndarray, station_name: str, rcu_mode: Union[str, int],
                      subband: int, caltable_dir: str = "CalTables"):
    """
    Apply calibration to visibilities

    Args:
        visibilities (np.ndarray): Visibility cube
        station_name (str): Station name, e.g. "DE603"
        rcu_mode (Union[str, int]): RCU mode, e.g. 5
        subband (int): Subband
        caltable_dir (str, optional): Directory with calibration tables. Defaults to "CalTables".

    Returns:
        Tuple[np.ndarray, Dict[str, str]]: modified visibilities and dictionary with calibration info
    """
    caltable_filename = find_caltable(station_name, rcu_mode=rcu_mode,
                                      caltable_dir=caltable_dir)
    cal_header = {}
    if caltable_filename is None:
        print('No calibration table found... cube remains uncalibrated!')
    else:
        cal_header, cal_data = read_caltable(caltable_filename)

        rcu_gains = cal_data[subband, :]
        rcu_gains = np.array(rcu_gains, dtype=np.complex64)
        gain_matrix = rcu_gains[np.newaxis, :] * np.conj(rcu_gains[:, np.newaxis])
        visibilities = visibilities / gain_matrix

    return visibilities, cal_header


def rcus_in_station(station_type: str):
    """
    Give the number of RCUs in a station, given its type.

    Args:
        station_type: Kind of station that produced the correlation. One of
            'core', 'remote', 'intl'.

    Example:
        >>> rcus_in_station('remote')
        96
    """
    return {'core': 96, 'remote': 96, 'intl': 192}[station_type]


def get_station_type(station_name: str) -> str:
    """
    Get the station type, one of 'intl', 'core' or 'remote'

    Args:
        station_name: Station name, e.g. "DE603LBA" or just "DE603"

    Returns:
        str: station type, one of 'intl', 'core' or 'remote'

    Example:
        >>> get_station_type("DE603")
        'intl'
    """
    if station_name[0] == "C":
        return "core"
    elif station_name[0] == "R" or station_name[:5] == "PL611":
        return "remote"
    else:
        return "intl"


def get_station_pqr(station_name: str, rcu_mode: Union[str, int], db):
    """
    Get PQR coordinates for the relevant subset of antennas in a station.

    Args:
        station_name: Station name, e.g. 'DE603LBA' or 'DE603'
        rcu_mode: RCU mode (0 - 6, can be string)
        db: instance of LofarAntennaDatabase from lofarantpos

    Example:
        >>> from lofarantpos.db import LofarAntennaDatabase
        >>> db = LofarAntennaDatabase()
        >>> pqr = get_station_pqr("DE603", "outer", db)
        >>> pqr.shape
        (96, 3)
        >>> pqr[0, 0]
        np.float32(1.7434713)

        >>> pqr = get_station_pqr("LV614", "5", db)
        >>> pqr.shape
        (96, 3)
    """
    full_station_name = get_full_station_name(station_name, rcu_mode)
    station_type = get_station_type(full_station_name)

    if 'LBA' in station_name or str(rcu_mode) in ('1', '2', '3', '4', 'inner', 'outer', 'sparse_even', 'sparse_odd', 'sparse'):
        if (station_type == 'core' or station_type == 'remote'):
            if str(rcu_mode) in ('3', '4', 'inner'):
                station_pqr = db.antenna_pqr(full_station_name)[0:48, :]
            elif str(rcu_mode) in ('1', '2', 'outer'):
                station_pqr = db.antenna_pqr(full_station_name)[48:, :]
            elif rcu_mode in ('sparse_even', 'sparse'):
                all_pqr = db.antenna_pqr(full_station_name)
                # Indices 0, 49, 2, 51, 4, 53, ...
                station_pqr = np.ravel(np.column_stack((all_pqr[:48:2], all_pqr[49::2]))).reshape(48, 3)
            elif rcu_mode == 'sparse_odd':
                all_pqr = db.antenna_pqr(full_station_name)
                # Indices 1, 48, 3, 50, 5, 52, ...
                station_pqr = np.ravel(np.column_stack((all_pqr[1:48:2], all_pqr[48::2]))).reshape(48, 3)
            else:
                raise RuntimeError("Cannot select subset of LBA antennas for mode " + rcu_mode)
        else:
            station_pqr = db.antenna_pqr(full_station_name)
    elif 'HBA' in station_name or str(rcu_mode) in ('5', '6', '7', '8'):
        selected_dipole_config = {
            'intl': GENERIC_INT_201512, 'remote': GENERIC_REMOTE_201512, 'core': GENERIC_CORE_201512
        }
        selected_dipoles = selected_dipole_config[station_type] + \
            np.arange(len(selected_dipole_config[station_type])) * 16
        station_pqr = db.hba_dipole_pqr(full_station_name)[selected_dipoles]
    else:
        raise RuntimeError("Station name did not contain LBA or HBA, could not load antenna positions")

    return station_pqr.astype('float32')


def get_station_xyz(station_name: str, rcu_mode: Union[str, int], db):
    """
    Get XYZ coordinates for the relevant subset of antennas in a station.
    The XYZ system is defined as the PQR system rotated along the R axis to make
    the Q-axis point towards local north.

    Args:
        station_name: Station name, e.g. 'DE603LBA' or 'DE603'
        rcu_mode: RCU mode (0 - 6, can be string)
        db: instance of LofarAntennaDatabase from lofarantpos

    Returns:
        np.array: Antenna xyz, shape [n_ant, 3]
        np.array: rotation matrix pqr_to_xyz, shape [3, 3]

    Example:
        >>> from lofarantpos.db import LofarAntennaDatabase
        >>> db = LofarAntennaDatabase()
        >>> xyz, _ = get_station_xyz("DE603", "outer", db)
        >>> xyz.shape
        (96, 3)
        >>> f"{xyz[0, 0]:.7f}"
        '2.7033776'

        >>> xyz, _ = get_station_xyz("LV614", "5", db)
        >>> xyz.shape
        (96, 3)
    """
    station_pqr = get_station_pqr(station_name, rcu_mode, db)

    station_name = get_full_station_name(station_name, rcu_mode)

    rotation = db.rotation_from_north(station_name)

    pqr_to_xyz = np.array([[np.cos(-rotation), -np.sin(-rotation), 0],
                           [np.sin(-rotation), np.cos(-rotation), 0],
                           [0, 0, 1]])

    station_xyz = (pqr_to_xyz @ station_pqr.T).T

    return station_xyz, pqr_to_xyz


def get_full_station_name(station_name: str, rcu_mode: Union[str, int]) -> str:
    """
    Get full station name with the field appended, e.g. DE603LBA

    Args:
        station_name (str): Short station name, e.g. 'DE603'
        rcu_mode (Union[str, int]): RCU mode

    Returns:
        str: Full station name, e.g. DE603LBA

    Example:
        >>> get_full_station_name("DE603", '3')
        'DE603LBA'

        >>> get_full_station_name("LV614", 5)
        'LV614HBA'

        >>> get_full_station_name("CS013LBA", 1)
        'CS013LBA'

        >>> get_full_station_name("CS002", 1)
        'CS002LBA'
    """
    if len(station_name) > 5:
        return station_name

    if str(rcu_mode) in ('1', '2', 'outer'):
        station_name += "LBA"
    elif str(rcu_mode) in ('3', '4', 'inner'):
        station_name += "LBA"
    elif 'sparse' in str(rcu_mode):
        station_name += "LBA"
    elif str(rcu_mode) in ('5', '6', '7'):
        station_name += "HBA"
    else:
        raise Exception("Unexpected rcu_mode: ", rcu_mode)

    return station_name

def make_sky_movie(moviefilename: str, h5file: h5py.File, obsnums: List[str], vmin=None, vmax=None,
                   marked_bodies=["Cas A", "Cyg A", "Sun"]) -> None:
    """
    Make movie of a list of observations
    """
    fig = plt.figure(figsize=(10,10))
    for obsnum in tqdm.tqdm(obsnums):
        obs_h5 = h5file[obsnum]
        skydata_h5 = obs_h5["sky_img"]
        obstime = obs_h5.attrs["obstime"]
        freq = obs_h5.attrs["frequency"]
        station_name = obs_h5.attrs["station_name"]
        subband = obs_h5.attrs["subband"]
        marked_bodies_lmn = {
            name: {
                'lmn': lmn,
                'elevation': elevation,
                'azimuth': azimuth
            }
            for name, lmn, elevation, azimuth in zip(
                obs_h5.attrs["source_names"], 
                obs_h5.attrs["source_lmn"], 
                obs_h5.attrs["source_elevations"], 
                obs_h5.attrs["source_azimuths"]
            )
        }

        bodies_info = "\n".join(
            [f"{name}: Elevation {data['elevation']:.2f}°, Azimuth {data['azimuth']:.2f}°"
            for name, data in marked_bodies_lmn.items()]
        )

        subtitle_text = (f"SB {subband} ({freq / 1e6:.1f} MHz), {str(obstime)[:16]}\n" + bodies_info)
        
        # if marked_bodies is not None:
        #     marked_bodies_lmn = {k: v for k, v in marked_bodies_lmn.items() if k in marked_bodies}
        make_sky_plot(skydata_h5[:, :], marked_bodies_lmn,
                      title=f"Sky image for {station_name}",
                      subtitle=subtitle_text,
                      animated=True, fig=fig, label=obsnum, vmin=vmin, vmax=vmax)

    # Thanks to Maaijke Mevius for making this animation work!
    ims = fig.get_children()[1:]
    ims = [ims[i:i+2] for i in range(0, len(ims), 2)]
    ani = matplotlib.animation.ArtistAnimation(fig, ims, interval=30, blit=False, repeat_delay=1000)
    writer = matplotlib.animation.writers['ffmpeg'](fps=5, bitrate=800)
    ani.save(moviefilename, writer=writer, dpi=fig.dpi)


def reimage_sky(h5: h5py.File, obsnum: str, db: lofarantpos.db.LofarAntennaDatabase,
                subtract: List[str] = None, vmin: float = None, vmax: float = None):
    """
    Reimage the sky for one observation in an HDF5 file

    Args:
        h5 (h5py.File): HDF5 file
        obsnum (str): observation number
        db (lofarantpos.db.LofarAntennaDatabase): instance of lofar antenna database
        subtract (List[str], optional): List of sources to subtract, e.g. ["Cas A", "Sun"]

    Returns:
        matplotlib.Figure

    Example:
        >>> from lofarantpos.db import LofarAntennaDatabase
        >>> db = LofarAntennaDatabase()
        >>> fig = reimage_sky(h5py.File("test/test.h5", "r"), "obs000002", db, subtract=["Cas A"])
    """
    station_name = h5[obsnum].attrs['station_name']
    subband = h5[obsnum].attrs['subband']
    obstime = h5[obsnum].attrs['obstime']
    rcu_mode = h5[obsnum].attrs['rcu_mode']
    sky_data = h5[obsnum]["sky_img"]
    freq = h5[obsnum].attrs['frequency']
    marked_bodies_lmn = dict(zip(h5[obsnum].attrs["source_names"], h5[obsnum].attrs["source_lmn"]))
    visibilities = h5[obsnum]['calibrated_data'][:]
    visibilities_xx = visibilities[0::2, 0::2]
    visibilities_yy = visibilities[1::2, 1::2]
    # Stokes I
    visibilities_stokes_i = visibilities_xx + visibilities_yy

    if subtract is not None:
        station_xyz, _ = get_station_xyz(station_name, rcu_mode, db)
        baselines = station_xyz[:, np.newaxis, :] - station_xyz[np.newaxis, :, :]
        visibilities_stokes_i = subtract_sources(visibilities_stokes_i, baselines, freq, marked_bodies_lmn, subtract)
        sky_data = sky_imager(visibilities_stokes_i, baselines, freq, sky_data.shape[0], sky_data.shape[1])
        if vmin is None:
            vmin = np.quantile(sky_data, 0.05)

    sky_fig = make_sky_plot(sky_data, {k: v for k, v in marked_bodies_lmn.items()},
                            title=f"Sky image for {station_name}",
                            subtitle=f"SB {subband} ({freq / 1e6:.1f} MHz), {str(obstime)[:16]}",
                            vmin=vmin, vmax=vmax)

    return sky_fig