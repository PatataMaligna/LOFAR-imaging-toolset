from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)

from PyQt6.QtCore import pyqtSignal
from realtime_processor.plot import Plot
from datetime import datetime
from threading import Lock
import time
class MainWindow(QMainWindow):
    """Main window for the real-time plot."""

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
        # subtitle = datetime.now().strftime('%H:%M:%S')
        self.plot_widget.plot_matrix(covariance_matrix, dat_path, subband, rcu_mode, vmin=None, vmax=None)
        ##Signal to indicate that the plot has been drawn
        self.plot_ready.emit() 

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