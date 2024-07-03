import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QPainterPath, QPolygon, QFont
from PySide6.QtCore import Qt, QPoint, QRect

class ButtonEditor(QMainWindow):
    def __init__(self, path_planner):
        super().__init__()
        self.setWindowTitle("Button Editor")
        self.path_planner = path_planner

        #Set background image to the field
        self.image_label = QLabel(self)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "Field.png")
        self.pixmap = QPixmap(image_path)
        
        if self.pixmap.isNull():
            self.image_label.setText(f"Image not found at: {image_path}")
        else:
            self.image_label.setPixmap(self.pixmap)

        #Layout stuff
        self.path_planner_button = QPushButton("Main Window")
        self.path_planner_button.clicked.connect(self.show_path_planner)
        self.button_editor_button = QPushButton("Button Editor")
        self.button_editor_button.clicked.connect(self.show_button_editor)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.path_planner_button)
        button_layout.addWidget(self.button_editor_button)

        #Layout of the auto planner
        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.image_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 60)

    def show_button_editor(self):
        self.show()
        self.path_planner.hide()

    def show_path_planner(self):
        self.hide()
        self.path_planner.show()