import os
import time
import numpy as np

def wait_for_dat_file(input_dir):
    """Waits until a .dat file appears in the input directory."""
    dat_file = None
    while not dat_file:
        files = [f for f in os.listdir(input_dir) if f.endswith("_xst.dat")]
        if files:
            dat_file = os.path.join(input_dir, files[0])
        else:
            print("Waiting for .dat file")
            time.sleep(1)
    return dat_file

def detect_new_data_from_stream(f, last_size, num_rcu=192):
    """
    Reads new data from the .dat file in fixed-size chunks.

    Args:
        f (file object): Open file object for the .dat file.
        last_size (int): Last read position in the file.
        num_rcu (int): Number of RCUs (default: 192).

    Returns:
        np.ndarray: The next covariance matrix as a 2D array.
        int: The updated file size (new last position).
    """
    matrix_size_bytes = num_rcu * num_rcu * np.dtype(np.complex128).itemsize

    f.seek(0, os.SEEK_END)
    current_size = f.tell()

    if current_size <= last_size:
        return None, last_size

    f.seek(last_size)
    if last_size + matrix_size_bytes <= current_size:
        chunk = np.fromfile(f, dtype=np.complex128, count=num_rcu * num_rcu)
        chunk = chunk.reshape((num_rcu, num_rcu))
        last_size += matrix_size_bytes
        return chunk, last_size
    else:
        return None, last_size