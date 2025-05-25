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

def detect_new_data_from_stream(f, last_size, num_rcu=192, realtime_mode=False, last_time=None):
    """
    Reads new data from the .dat file in fixed-size chunks.

    Args:
        f (file object): Open file object for the .dat file.
        last_size (int): Last read position in the file.
        num_rcu (int): Number of RCUs (default: 192).

    Returns:
        np.ndarray or None: The next covariance matrix as a 2D array, or None if end of file.
        int: The updated file size (new last position).
    """
    matrix_size_bytes = num_rcu * num_rcu * np.dtype(np.complex128).itemsize

    chunk_bytes = f.read(matrix_size_bytes)
    if not chunk_bytes or len(chunk_bytes) < matrix_size_bytes:
        return None, last_size, last_time

    chunk = np.frombuffer(chunk_bytes, dtype=np.complex128, count=num_rcu * num_rcu)
    chunk = chunk.reshape((num_rcu, num_rcu))

    now = time.time()
    speed = None
    if last_time is not None:
        speed = now - last_time
        print(f"Time since last chunk: {speed:.3f} seconds")
    last_time = now

    if realtime_mode and last_size > 0:
        print(f"Current arrays read: {last_size / matrix_size_bytes}")
    last_size += matrix_size_bytes
    print(f"Reading at position {f.tell()}")
    # print(chunk)
    return chunk, last_size, last_time

def get_data_from_subband(f, inputSubband, min_subband, max_subband, num_rcu=192):
    """
    Reads the specific array covariance for this specific subband

    Args:
        f (file object): Open file object for the .dat file.
        subband (int): The subband to read data from.

    Returns:
        np.ndarray or None: The covariance matrix for the specified subband, or None if not found.
    """
    matrix_size_bytes = num_rcu * num_rcu * np.dtype(np.complex128).itemsize
    # Seek to the position of the subband
    f.seek((inputSubband - min_subband) * matrix_size_bytes)
    print(f"Reading subband {inputSubband - min_subband} at position {f.tell()}")
    chunk_bytes = f.read(matrix_size_bytes)
    chunk = np.frombuffer(chunk_bytes, dtype=np.complex128, count=num_rcu * num_rcu)
    chunk = chunk.reshape((num_rcu, num_rcu))
    
    return chunk
