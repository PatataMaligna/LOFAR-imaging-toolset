import time
import os
import sys
from datetime import datetime
from realtime_processor.monitor import wait_for_dat_file, detect_new_data
from realtime_processor.processor import process_data, get_obstime, get_subband, get_subband_from_shell

def main():
    """Main loop to process real-time data and generate images."""
    if len(sys.argv) < 2:
        print("No directory in the input")
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

    print(f"Output directory: {output_dir}")

    processed_files = {}  # Dictionary to track processed files and their last modification times
    timeout = 15 

    while True:
        dat_files = [f for f in os.listdir(input_dir) if f.endswith(".dat")]
        new_files = []

        # Check for new files
        for dat_file in dat_files:
            dat_path = os.path.join(input_dir, dat_file)
            last_modified = os.path.getmtime(dat_path)

            if dat_file not in processed_files or processed_files[dat_file] < last_modified:
                new_files.append(dat_file)
                processed_files[dat_file] = last_modified

        if not new_files:
            print("No new .dat files found. Waiting...")
            time.sleep(5)
            timeout -= 5
            if timeout <= 0:
                print("No new data for " + timeout + " seconds, stopping script.")
                break
            continue

        for dat_file in new_files:
            dat_path = os.path.join(input_dir, dat_file)
            header_file = dat_path.replace(".dat", ".h")

            if os.path.exists(header_file):
                subband = get_subband(header_file)
            else:
                subband = get_subband_from_shell(shell_script)

            if isinstance(subband, tuple) and len(subband) == 2:
                subband1, subband2 = subband
                case_b = True
                print(f"Processing {dat_file} | Subbands: {subband1}, {subband2}")
            else:
                case_b = False
                print(f"Processing {dat_file} | Subband: {subband}")

            last_size = 0
            start_time = time.time()
            timeout = 15  # Stop if no new data arrives for timeout seconds

            while time.time() - start_time < timeout:
                covariance_matrix, last_size = detect_new_data(dat_path, last_size)
                if covariance_matrix is not None:
                    if case_b and subband1 <= subband2:
                        image_data = process_data(covariance_matrix, subband1, dat_path = dat_path, output_dir=output_dir)
                        subband1 += 1
                    if not case_b:
                        image_data = process_data(covariance_matrix, subband, dat_path = dat_path, output_dir=output_dir)
                    start_time = time.time() 
                time.sleep(1)


        create_video(output_dir, os.path.join(output_dir, "output_video.mp4"))

if __name__ == "__main__":
    main()
