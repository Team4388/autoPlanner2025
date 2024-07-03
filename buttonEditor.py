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

        self.image_label = QLabel(self)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "Field.png")
        self.pixmap = QPixmap(image_path)
        
        if self.pixmap.isNull():
            self.image_label.setText(f"Image not found at: {image_path}")
        else:
            self.image_label.setPixmap(self.pixmap)

        self.path_planner_button = QPushButton("Main Window")
        self.path_planner_button.clicked.connect(self.show_path_planner)
        self.button_editor_button = QPushButton("Button Editor")
        self.button_editor_button.clicked.connect(self.show_button_editor)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.path_planner_button)
        button_layout.addWidget(self.button_editor_button)

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

    def update_scene(self):
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        grey_pen = QPen(QColor(127, 127, 127))
        grey_pen.setWidth(2)
        painter.setPen(grey_pen)

        # Draw the Bezier curve segments
        if self.path_planner.coordinates.size > 0:
            for i in range(len(self.path_planner.coordinates) - 1):
                start = QPoint(self.path_planner.coordinates[i][0], self.path_planner.coordinates[i][1])
                end = QPoint(self.path_planner.coordinates[i + 1][0], self.path_planner.coordinates[i + 1][1])

                if i < len(self.path_planner.control_points):
                    control_pair = self.path_planner.control_points[i]

                    pen = QPen(Qt.yellow)
                    pen.setWidth(2)
                    painter.setPen(pen)

                    path = QPainterPath()
                    path.moveTo(start)
                    path.cubicTo(control_pair[0], control_pair[1], end)
                    painter.drawPath(path)

        # Draw the nodes
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSize(25)
        painter.setFont(font)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)

        for i, (x, y) in enumerate(self.path_planner.coordinates):
            node_rect = QRect(x - self.path_planner.node_size // 2, y - self.path_planner.node_size // 2,
                            self.path_planner.node_size, self.path_planner.node_size)
            painter.drawEllipse(node_rect)
            painter.drawText(node_rect, Qt.AlignCenter, str(i + 1))

        painter.end()
        self.image_label.setPixmap(self.pixmap)
