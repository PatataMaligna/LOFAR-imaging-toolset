import time
import os
import sys
from datetime import datetime
from realtime_processor.monitor import wait_for_dat_file, detect_new_data
from realtime_processor.processor import process_data, get_obstime, get_subband, get_subband_from_shell, obs_parser

def main():
    """Main loop to process real-time data and generate images."""
    if len(sys.argv) < 2:
        print("Usage: realtime-processor <input_folder>")
        sys.exit(1)

    input_dir = sys.argv[1]

    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    shell_script = None
    for file in os.listdir(input_dir):
        if file.endswith(".sh"):
            shell_script = os.path.join(input_dir, file)
            break

    # Generate output folder name based on the current date
    today_date = datetime.today().strftime('%Y-%m-%d')
    output_dir = os.path.join(input_dir, f"{today_date}_realtime_observation")
    os.makedirs(output_dir, exist_ok=True)

    print(f"SOutput directory: {output_dir}")

    img_number = 0

    while True:
        dat_files = [f for f in os.listdir(input_dir) if f.endswith(".dat")]
        if not dat_files:
            print("No .dat files found. Waiting...")
            time.sleep(5)
            continue

        for dat_file in dat_files:
            dat_path = os.path.join(input_dir, dat_file)
            header_file = dat_path.replace(".dat", ".h")

            if os.path.exists(header_file):
                subband = get_subband(header_file)
            else:
                subband = get_subband_from_shell(shell_script)
            print(f"Processing {dat_file} | Subband: {subband}")

            last_size = 0
            start_time = time.time()
            timeout = 15  # Stop if no new data arrives for timeout seconds

            while time.time() - start_time < timeout:
                # print("waiting for new data")
                covariance_matrix, last_size = detect_new_data(dat_path, last_size)
                if covariance_matrix is not None:
                    img_number += 1
                    image_data = process_data(covariance_matrix, subband, dat_path = dat_path, output_dir=output_dir, frame=img_number)
                    start_time = time.time() 
                time.sleep(1)


        create_video(output_dir, os.path.join(output_dir, "output_video.mp4"))

if __name__ == "__main__":
    main()
