import sys
import os
import argparse
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread
from realtime_processor.mainWindow import MainWindow
from realtime_processor.worker import DataProcessorWorker
def main():
    parser = argparse.ArgumentParser(description="LOFAR Imaging Processor")
    parser.add_argument("data_path", help="Path to data directory")
    parser.add_argument("--realtime", action="store_true", help="Enable real-time observation mode")
    args = parser.parse_args()

    input_dir = args.data_path

    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    if args.realtime:
        print("Running in real-time mode")

    else:
        print("Running in local mode")

    today_date = datetime.today().strftime('%Y-%m-%d')
    output_dir = os.path.join(input_dir, f"{today_date}_realtime_observation")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Output directory: {output_dir}")

    app = QApplication(sys.argv) 
    from threading import Event
    window = MainWindow(realtime_mode=args.realtime)
    window.show()

    # QThread setup
    thread = QThread()
    worker = DataProcessorWorker(input_dir, output_dir, realtime_mode=args.realtime)
    worker.moveToThread(thread)
    
    thread.started.connect(worker.run)

    window.frequency_signal.connect(worker.on_frequency_update)
    window.continue_same_freq_signal.connect(worker.on_continue_same_freq)
    window.continue_incr_freq_signal.connect(worker.on_continue_incr_freq)
    worker.update_signal.connect(window.update_plot)
    window.plot_ready.connect(worker.on_plot_ready)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    worker.finished.connect(app.quit)
    
    thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
