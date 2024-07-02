import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QPen
from PySide6.QtCore import Qt, QPoint, QRect

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Auto Planner")

        #Set background image to the field
        self.image_label = QLabel(self)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "Field.png")
        self.pixmap = QPixmap(image_path)
        
        if self.pixmap.isNull():
            self.image_label.setText(f"Image not found at: {image_path}")
        else:
            self.image_label.setPixmap(self.pixmap)

        #Buttons
        self.clear_button = QPushButton("Clear Auto")
        self.clear_button.clicked.connect(self.clear_points)

        #Layout of the auto planner
        layout = QVBoxLayout()
        layout.addWidget(self.clear_button)
        layout.addWidget(self.image_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 60)

        self.setMouseTracking(True)

        #Variables
        self.coordinates = np.empty((0, 2), dtype=int)
        self.robot_size = 35

    #Tell where the user clicked the screen
    def mousePressEvent(self, event: QMouseEvent):
        pos = self.image_label.mapFrom(self, event.position().toPoint())
        x = pos.x()
        y = pos.y()
        
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            self.coordinates = np.vstack((self.coordinates, [x, y]))

            if event.button() == Qt.RightButton:
                self.instantiate_robot()
                print(f"{self.coordinates}")

    #Create a robot(square) at the point clicked
    def instantiate_robot(self):
        painter = QPainter(self.pixmap)
        pen = QPen(Qt.white)
        pen.setWidth(2)
        painter.setPen(pen)
        

        if len(self.coordinates) > 1:
            for i in range(len(self.coordinates) - 1):
                x1, y1 = self.coordinates[i]
                x2, y2 = self.coordinates[i + 1]
                painter.drawLine(x1, y1, x2, y2)
        
        #Create robot
        for x, y in self.coordinates:
            top_left_x = int(x - self.robot_size // 2)
            top_left_y = int(y - self.robot_size // 2)
            
            painter.drawRect(QRect(top_left_x, top_left_y, self.robot_size, self.robot_size))
        
        self.image_label.setPixmap(self.pixmap)

    #Clears all points
    def clear_points(self):
        self.coordinates = np.empty((0, 2), dtype=int)
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        self.image_label.setPixmap(self.pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())