import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread
from realtime_processor.mainWindow import MainWindow
from realtime_processor.worker import DataProcessorWorker
def main():
    if len(sys.argv) < 2:
        print("No directory in the input")
        sys.exit(1)

    input_dir = sys.argv[1]
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    today_date = datetime.today().strftime('%Y-%m-%d')
    output_dir = os.path.join(input_dir, f"{today_date}_realtime_observation")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Output directory: {output_dir}")

    app = QApplication(sys.argv) 
    from threading import Event
    window = MainWindow()
    window.show()

    # QThread setup
    thread = QThread()
    worker = DataProcessorWorker(input_dir, output_dir)
    worker.moveToThread(thread)
    
    thread.started.connect(worker.run)

    window.frequency_signal.connect(worker.on_frequency_update)
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
