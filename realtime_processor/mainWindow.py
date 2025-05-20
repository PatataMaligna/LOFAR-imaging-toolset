from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)
from PyQt6.QtCore import QThread, pyqtSignal
from realtime_processor.plot import Plot
from realtime_processor.plotWorker import PlotWorker
class MainWindow(QMainWindow):
    """Main window for the real-time plot."""
    plot_drawn = pyqtSignal(object)
    plot_ready = pyqtSignal()
    frequency_signal = pyqtSignal(str)
    update_signal = pyqtSignal(object, str, int, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Plot image")
        self.setGeometry(0, 0, 1024, 768)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        outer_layout = QHBoxLayout(self.central_widget)

        control_layout = QVBoxLayout()
        self.frequency_label = QLabel("Enter Frequency (10 - 99) MHz:")
        control_layout.addWidget(self.frequency_label)

        self.frequency_input = QLineEdit()
        control_layout.addWidget(self.frequency_input)

        self.submit_button = QPushButton("Submit Frequency")
        control_layout.addWidget(self.submit_button)

        ##Push the button + text upp
        control_layout.addStretch()

        self.submit_button.clicked.connect(self.submit_frequency)

        self.plot_widget = Plot()

        # Add widgets to the outer layout
        outer_layout.addLayout(control_layout, stretch=1)
        outer_layout.addWidget(self.plot_widget, stretch=4)

        self.update_signal.connect(self.update_plot)

    def update_plot(self, covariance_matrix, dat_path, subband = None, rcu_mode = "3"):
        """Update the plot with a new matrix."""
        self.plot_worker = PlotWorker(covariance_matrix, dat_path, subband, rcu_mode)
        self.plot_thread = QThread()
        self.plot_worker.moveToThread(self.plot_thread)

        self.plot_thread.started.connect(self.plot_worker.run)
        self.plot_worker.plot_drawn.connect(self.on_plot_ready)
        self.plot_worker.plot_drawn.connect(self.plot_thread.quit)
        self.plot_worker.plot_drawn.connect(self.plot_worker.deleteLater)
        self.plot_thread.finished.connect(self.plot_thread.deleteLater)
        self.plot_thread.start()

    def on_plot_ready(self, sky_fig):
        """Handle the plot when it's ready."""
        self.plot_widget = sky_fig
        self.plot_ready.emit()
        self.plot_thread.quit()

    def submit_frequency(self):
        """Submit the frequency input."""
        try:
            freq = float(self.frequency_input.text())
            if 10 <= freq <= 99:
                self.selected_frequency = str(freq)
                self.frequency_signal.emit(str(freq))
            else:
                print("Frequency must be between 10 and 99 MHz.")
        except ValueError:
            print("Invalid frequency input.")