from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QGroupBox, QVBoxLayout, QCheckBox
)

from PyQt6.QtCore import pyqtSignal, QCoreApplication
from realtime_processor.plot import Plot
from datetime import datetime
from threading import Lock
import time
import configparser
import os
class MainWindow(QMainWindow):
    """Main window for the real-time plot."""

    plot_ready = pyqtSignal()
    frequency_signal = pyqtSignal(str)
    update_signal = pyqtSignal(object, str, int, str, datetime)
    continue_same_freq_signal = pyqtSignal()
    continue_incr_freq_signal = pyqtSignal()

    def __init__(self, realtime_mode=False):
        super().__init__()
        self.setWindowTitle("Real-Time Plot image")
        self.setGeometry(0, 0, 1024, 768)
        # Read sources from sources.ini
        config = configparser.ConfigParser()
        config.read("./sources.ini")
        self.sources = sorted(config.sections())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        outer_layout = QHBoxLayout(self.central_widget)

        control_layout = QVBoxLayout()
        if not realtime_mode:
            self.frequency_label = QLabel("Enter Frequency (10 - 99) MHz:")
            control_layout.addWidget(self.frequency_label)

            self.frequency_input = QLineEdit()
            control_layout.addWidget(self.frequency_input)

            self.submit_button = QPushButton("Submit Frequency")
            control_layout.addWidget(self.submit_button)

            # Add new buttons below the frequency input
            self.continue_same_freq_button = QPushButton("Continue same frequency")
            control_layout.addWidget(self.continue_same_freq_button)

            self.continue_incr_freq_button = QPushButton("Continue increasing frequency")
            control_layout.addWidget(self.continue_incr_freq_button)

            ##Push the button + text upp
            control_layout.addStretch()
            self.submit_button.clicked.connect(self.submit_frequency)
            self.continue_same_freq_button.clicked.connect(self.continue_same_freq_signal.emit)
            self.continue_incr_freq_button.clicked.connect(self.continue_incr_freq_signal.emit)

        self.sources_group = QGroupBox("Show Sources")
        self.sources_layout = QVBoxLayout()
        self.source_checkboxes = {}
        for source in self.sources:
            cb = QCheckBox(source)
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_sources_changed)
            self.sources_layout.addWidget(cb)
            self.source_checkboxes[source] = cb
        self.sources_group.setLayout(self.sources_layout)
        control_layout.addWidget(self.sources_group)

        

        self.plot_widget = Plot()

        # Add widgets to the outer layout
        outer_layout.addLayout(control_layout, stretch=1)
        outer_layout.addWidget(self.plot_widget, stretch=4)

        self.update_signal.connect(self.update_plot)

    def update_plot(self, covariance_matrix, dat_path, subband = None, rcu_mode = "3", obstime = None):
        """Update the plot with a new matrix."""
        self.plot_widget.plot_matrix(covariance_matrix, dat_path, subband, rcu_mode, obstime,
                                    sources_to_display=self.sources, vmin=None, vmax=None)
        QCoreApplication.processEvents()
        ##Signal to indicate that the plot has been drawn
        self.plot_ready.emit() 

    def submit_frequency(self):
        """Submit the frequency input."""
        try:
            freq = float(self.frequency_input.text())
            if 10 <= freq <= 99:
                self.selected_frequency = str(freq)
                self.frequency_signal.emit(str(freq))
                self.frequency_input.setText("")
            else:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Frequency", "Please enter a frequency between 10 and 99 MHz.")

    def on_sources_changed(self):
        selected_sources = []
        for name, cb in self.source_checkboxes.items():
            if cb.isChecked():
                selected_sources.append(name)
        self.sources = selected_sources