import os
import time
from datetime import datetime, timedelta
from tqdm import tqdm
from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
from realtime_processor.monitor import detect_new_data_from_stream, get_data_from_subband
from realtime_processor.processor import get_subband, get_subband_from_shell, get_rcu_mode
from realtime_processor.singlestationutil import sb_from_freq
# from .video import create_video

class DataProcessorWorker(QObject):
    update_signal = pyqtSignal(object, str, int, str, datetime)
    finished = pyqtSignal()
    frequency_signal = pyqtSignal(str)
    
    def __init__(self, input_dir, output_dir, realtime_mode=False):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.waiting_for_plot = True
        self.selected_frequency = None
        self.realtime_mode = realtime_mode
        self.continue_same_freq = False
        self.continue_incr_freq = False

    def on_plot_ready(self):
        self.waiting_for_plot = False

    def on_frequency_update(self, freq):
        print(f"Frequency updated to: {freq}")
        self.selected_frequency = freq

    def on_continue_same_freq(self):
        print("Continuing with the same frequency.")
        self.continue_same_freq = True

    def on_continue_incr_freq(self):
        print("Continuing with the increased frequency.")
        self.continue_incr_freq = True

    def get_obstime_from_filename(self, dat_path):
        basename = os.path.basename(dat_path)
        obsdatestr, obstimestr, *_ = basename.rstrip(".dat").split("_")
        return datetime.strptime(obsdatestr + ":" + obstimestr, '%Y%m%d:%H%M%S')

    def run(self):
        if self.realtime_mode:
            
            shell_script = None
            for file in os.listdir(self.input_dir):
                if file.endswith(".sh"):
                    shell_script = os.path.join(self.input_dir, file)
                    print(f"Shell script found: {shell_script}")
                    break
            if not shell_script:
                print("No shell script found.")
                ##DEFAULT parameters
                rcu_mode = "3"
                min_subband, max_subband = 51, 461
            else:
                rcu_mode = get_rcu_mode(shell_script)
                min_subband, max_subband = get_subband_from_shell(shell_script)

            ## INICITALIZE VARIABLES
            dat_files = [f for f in os.listdir(self.input_dir) if f.endswith(".dat")]
            if not dat_files:
                print("No .dat files found in the input directory.")
                self.finished.emit()
                return
            num_rcu = 192
            subband = min_subband
            last_size = 0
            last_time = None
            for dat_file in dat_files:
                dat_path = os.path.join(self.input_dir, dat_file)
                still_observing = True
                self.last_obstime = self.get_obstime_from_filename(dat_path)
                with open(dat_path, "rb") as f:
                    while still_observing:
                        covariance_matrix, last_size, last_time = detect_new_data_from_stream(f, last_size , num_rcu, realtime_mode=True, last_time=last_time)
                        if covariance_matrix is not None:
                            self.waiting_for_plot = True
                            if subband <= max_subband:
                                self.update_signal.emit(covariance_matrix, dat_path, subband, rcu_mode, self.last_obstime)
                                subband += 1
                            elif subband > max_subband:
                                subband = min_subband
                                self.update_signal.emit(covariance_matrix, dat_path, subband, rcu_mode, self.last_obstime)
                            while self.waiting_for_plot:
                                QCoreApplication.processEvents()                            
                                time.sleep(0.05)

                            self.last_obstime += timedelta(seconds=1)
                        else:
                            still_observing = False
            # create_video(self.output_dir, os.path.join(self.output_dir, f"generated_video.mp4"))
            self.finished.emit()
        else:
            shell_script = None
            for file in os.listdir(self.input_dir):
                if file.endswith(".sh"):
                    shell_script = os.path.join(self.input_dir, file)
                    break
            if not shell_script:
                print("No shell script found.")
                rcu_mode = "3"
            else:
                rcu_mode = get_rcu_mode(shell_script)
            processed_files = {}
            timeout = 15
            while True:
                dat_files = [f for f in os.listdir(self.input_dir) if f.endswith(".dat")]
                new_files = []
                print(f"Detected {len(dat_files)} .dat files.")
                for dat_file in dat_files:
                    dat_path = os.path.join(self.input_dir, dat_file)
                    last_modified = os.path.getmtime(dat_path)

                    if dat_file not in processed_files or processed_files[dat_file] < last_modified:
                        new_files.append(dat_file)
                        processed_files[dat_file] = last_modified
                    
                if not new_files:
                    print("No new .dat files found. Waiting...")
                    time.sleep(5)
                    timeout -= 5
                    if timeout <= 0:
                        print("Timeout. Exiting.")
                        break

                print(f"New files detected: {new_files}")

                for dat_file in new_files:
                    dat_path = os.path.join(self.input_dir, dat_file)
                    header_file = dat_path.replace(".dat", ".h")

                    self.last_obstime = self.get_obstime_from_filename(dat_path)
                    if shell_script:
                        subband = get_subband_from_shell(shell_script)
                        print(f"Subband from shell script: {subband}")
                    else:
                        subband = get_subband(header_file)

                    if isinstance(subband, tuple) and len(subband) == 2:
                        subband1, subband2 = subband
                        saved_subband = subband1
                        case_h = False  
                        print(f"Processing {dat_file} | Subbands: {subband1}, {subband2}")
                    else:
                        case_h = True
                        print(f"Processing {dat_file} | Subband: {subband}")

                    last_size = 0
                    last_time = None
                    file_size = os.path.getsize(dat_path)
                    still_observing = True
                    self.last_used_frequency = None
                    pbar = tqdm(total=file_size, desc="Analyzing File", unit="B", unit_scale=True, unit_divisor=1024)

                    with open(dat_path, "rb") as f:
                        while still_observing:
                            prev_size = last_size
                            covariance_matrix, last_size, last_time = detect_new_data_from_stream(f, last_size, last_time=last_time)
                            if covariance_matrix is not None:
                                self.waiting_for_plot = True
                                if self.continue_same_freq:
                                    definitive_subband = sb_from_freq(float(self.last_used_frequency) * 1e6, rcu_mode)
                                    self.update_signal.emit(covariance_matrix, dat_path, definitive_subband, rcu_mode, self.last_obstime)

                                if self.continue_incr_freq:
                                    if subband1 <= subband2:
                                        self.update_signal.emit(covariance_matrix, dat_path, subband1, rcu_mode, self.last_obstime)
                                        subband1 += 1
                                    elif subband1 > subband2:
                                        subband1 = saved_subband
                                        self.update_signal.emit(covariance_matrix, dat_path, subband1, rcu_mode, self.last_obstime)

                                if not case_h and not self.continue_same_freq and not self.continue_incr_freq:
                                    while (self.selected_frequency is None 
                                        or self.selected_frequency == self.last_used_frequency
                                    ):
                                        QCoreApplication.processEvents()
                                        time.sleep(0.1)
                                    # self.selected_frequency = "30"
                                    print(f"Selected frequency: {self.selected_frequency}")
                                    subband = sb_from_freq(float(self.selected_frequency) * 1e6, rcu_mode)
                                    print(f"Subband from frequency: {subband}")
                                    # covariance_matrix = get_data_from_subband(f, subband, subband1, subband2)
                                    self.update_signal.emit(covariance_matrix, dat_path, subband, rcu_mode, self.last_obstime)

                                    # Update last used frequency
                                    self.last_used_frequency = self.selected_frequency

                                elif case_h:
                                    self.update_signal.emit(covariance_matrix, dat_path, subband, rcu_mode, self.last_obstime)
                                
                                while self.waiting_for_plot:
                                    QCoreApplication.processEvents()                            
                                    time.sleep(0.05)

                                self.last_obstime += timedelta(seconds=1)
                                start_time = time.time()
                            else:
                                still_observing = False
                            pbar.update(last_size - prev_size)

            # create_video(self.output_dir, os.path.join(self.output_dir, f"generated_video.mp4"))
            self.finished.emit()
