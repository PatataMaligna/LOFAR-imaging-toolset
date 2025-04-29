import os
import time
from tqdm import tqdm
from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication
from realtime_processor.monitor import detect_new_data
from realtime_processor.processor import process_data, get_subband, get_subband_from_shell, get_rcu_mode
from lofarimaging import sb_from_freq

class DataProcessorWorker(QObject):
    update_signal = pyqtSignal(object, str, int, str)
    finished = pyqtSignal()
    frequency_signal = pyqtSignal(str)
    def __init__(self, input_dir, output_dir):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.waiting_for_plot = True
        self.selected_frequency = None

    def on_plot_ready(self):
        self.waiting_for_plot = False

    def on_frequency_update(self, freq):
        print(f"Frequency updated to: {freq}")
        self.selected_frequency = freq

    def run(self):
        shell_script = None
        for file in os.listdir(self.input_dir):
            if file.endswith(".sh"):
                shell_script = os.path.join(self.input_dir, file)
                break
        if not shell_script:
            print("No shell script found.")
            rcu_mode = "3"
            # self.finished.emit()
            # return
        else:
            rcu_mode = get_rcu_mode(shell_script)
        processed_files = {}
        timeout = 15

        while True:
            dat_files = [f for f in os.listdir(self.input_dir) if f.endswith(".dat")]
            new_files = []

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
                subband = get_subband(header_file) if os.path.exists(header_file) else get_subband_from_shell(shell_script)

                if isinstance(subband, tuple) and len(subband) == 2:
                    subband1, subband2 = subband
                    case_b = True
                    print(f"Processing {dat_file} | Subbands: {subband1}, {subband2}")
                else:
                    case_b = False
                    print(f"Processing {dat_file} | Subband: {subband}")

                last_size = 0
                start_time = time.time()
                timeout = 15
                file_size = os.path.getsize(dat_path)

                pbar = tqdm(total=file_size, desc="Analyzing File", unit="B", unit_scale=True, unit_divisor=1024)

                while time.time() - start_time < timeout:
                    prev_size = last_size
                    covariance_matrix, last_size = detect_new_data(dat_path, last_size)
                    if covariance_matrix is not None:
                        self.waiting_for_plot = True
                    
                        if self.selected_frequency is not None:
                            print(f"Selected frequency: {self.selected_frequency}")
                            subband = sb_from_freq(float(self.selected_frequency) * 1e6, rcu_mode)
                            print(f"Subband from frequency: {subband}")
                            self.update_signal.emit(covariance_matrix, dat_path, subband, rcu_mode)
                        elif case_b and subband1 <= subband2:
                            print("KALSDJFLKSADF", self.selected_frequency)
                            self.update_signal.emit(covariance_matrix, dat_path, subband1, rcu_mode)
                            subband1 += 1
                        elif not case_b:
                            # process_data(covariance_matrix, subband, dat_path=dat_path, output_dir=self.output_dir, rcu_mode=rcu_mode)
                            self.update_signal.emit(covariance_matrix, dat_path, subband, rcu_mode)

                        while self.waiting_for_plot:
                            QCoreApplication.processEvents()                            
                            time.sleep(1)

                        pbar.update(last_size - prev_size)
                        start_time = time.time()

        create_video(self.output_dir, os.path.join(self.output_dir, "output_video.mp4"))
        self.finished.emit()
