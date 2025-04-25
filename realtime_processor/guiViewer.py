import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer

class RealTimeViewer(QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        self.image_index = 0

        self.label = QLabel(self)
        self.label.setPixmap(QPixmap())

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1000)

        self.setWindowTitle("Real-Time Image Viewer")
        self.setGeometry(200, 200, 1024, 768)

    def update_image(self):
        images = sorted([f for f in os.listdir(self.image_folder) if f.endswith(".png")])
        if self.image_index < len(images):
            image_path = os.path.join(self.image_folder, images[self.image_index])
            pixmap = QPixmap(image_path)
            self.label.setPixmap(pixmap.scaled(self.label.size(), aspectRatioMode=True))
            self.image_index += 1