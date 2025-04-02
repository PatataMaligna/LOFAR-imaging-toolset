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

def detect_new_data(dat_file, last_size, num_rcu=192):
    """
    Reads new data from the .dat file in fixed-size chunks.

    Args:
        dat_file (str): Path to the .dat file.
        last_size (int): Last read position in the file.
        num_rcu (int): Number of RCUs (default: 192).

    Returns:
        np.ndarray: The next covariance matrix as a 2D array.
        int: The updated file size (new last position).
    """
    matrix_size_bytes = num_rcu * num_rcu * np.dtype(np.complex128).itemsize

    current_size = os.path.getsize(dat_file)

    if current_size <= last_size:
        return None, last_size

    with open(dat_file, "rb") as f:
        f.seek(last_size)  
        chunk = None
        if last_size + matrix_size_bytes <= current_size:
            chunk = np.fromfile(f, dtype=np.complex128, count=num_rcu * num_rcu)
            chunk = chunk.reshape((num_rcu, num_rcu))
            last_size += matrix_size_bytes
            print(f"Matrix size (bytes): {matrix_size_bytes}")
            print(f"Current file size: {current_size}, Last read position: {last_size}")
        else:
            print("Warning: Incomplete chunk detected. Ignoring until next read.")
            return None, last_size
    return chunk, last_size