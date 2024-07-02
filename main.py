import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt, QPoint, QRect

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Auto Planner")

        # Set background image to the field
        self.image_label = QLabel(self)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "Field.png")
        self.pixmap = QPixmap(image_path)
        
        if self.pixmap.isNull():
            self.image_label.setText(f"Image not found at: {image_path}")
        else:
            self.image_label.setPixmap(self.pixmap)

        # Buttons
        self.clear_button = QPushButton("Clear Auto")
        self.clear_button.clicked.connect(self.clear_points)

        # Layout of the auto planner
        layout = QVBoxLayout()
        layout.addWidget(self.clear_button)
        layout.addWidget(self.image_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 60)

        self.setMouseTracking(True)

        # Variables
        self.coordinates = np.empty((0, 2), dtype=int)
        self.robot_size = 35
        self.handle_size = 10
        self.handles = []
        self.dragging_handle = False
        self.dragging_handle_index = -1
        self.dragging_robot = False
        self.dragging_robot_index = -1

    def mousePressEvent(self, event: QMouseEvent):
        pos = self.image_label.mapFrom(self, event.position().toPoint())
        x, y = pos.x(), pos.y()
        
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            if event.button() == Qt.RightButton:
                self.coordinates = np.vstack((self.coordinates, [x, y]))
                if len(self.coordinates) >= 2:
                    self.calculate_handle_pos()
                self.draw_scene()
            elif event.button() == Qt.LeftButton:
                handle_index = self.is_point_in_handle(x, y)
                if handle_index != -1:
                    self.dragging_handle = True
                    self.dragging_handle_index = handle_index
                else:
                    robot_index = self.is_point_in_robot(x, y)
                    if robot_index != -1:
                        self.dragging_robot = True
                        self.dragging_robot_index = robot_index

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging_handle:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            self.handles[self.dragging_handle_index] = QPoint(x, y)
            self.draw_scene()
        elif self.dragging_robot:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            self.coordinates[self.dragging_robot_index] = [x, y]
            self.calculate_handle_pos()
            self.draw_scene()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging_handle = False
            self.dragging_handle_index = -1
            self.dragging_robot = False
            self.dragging_robot_index = -1

    def is_point_in_handle(self, x, y):
        for i, handle in enumerate(self.handles):
            if (abs(x - handle.x()) <= self.handle_size // 2 and
                abs(y - handle.y()) <= self.handle_size // 2):
                return i
        return -1

    def is_point_in_robot(self, x, y):
        for i, (robot_x, robot_y) in enumerate(self.coordinates):
            if (abs(x - robot_x) <= self.robot_size // 2 and
                abs(y - robot_y) <= self.robot_size // 2):
                return i
        return -1
    
    def calculate_handle_pos(self):
        if len(self.coordinates) >= 2:
            x1, y1 = self.coordinates[-2]
            x2, y2 = self.coordinates[-1]
            self.handles.append(QPoint((x1 + x2) // 2, (y1 + y2) // 2))

    def draw_scene(self):
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)
        pen = QPen(Qt.white)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.setBrush(Qt.NoBrush)  # Ensure no filling happens

        if len(self.coordinates) >= 2:
            for i in range(len(self.coordinates) - 1):
                start = QPoint(self.coordinates[i][0], self.coordinates[i][1])
                end = QPoint(self.coordinates[i + 1][0], self.coordinates[i + 1][1])
                
                if i < len(self.handles):
                    # Draw cubic Bezier curve
                    path = QPainterPath()
                    path.moveTo(start)
                    handle = self.handles[i]
                    path.cubicTo(
                        handle,  # Control point 1
                        handle,  # Control point 2
                        end      # End point
                    )
                    painter.drawPath(path)

                    # Draw handle
                    painter.setBrush(QColor(255, 255, 255))  # White color for handle
                    painter.drawRect(
                        handle.x() - self.handle_size // 2,
                        handle.y() - self.handle_size // 2,
                        self.handle_size,
                        self.handle_size
                    )
                    painter.setBrush(Qt.NoBrush)
                else:
                    painter.drawLine(start, end)

        # Create robots
        for i, (x, y) in enumerate(self.coordinates):
            top_left_x = int(x - self.robot_size // 2)
            top_left_y = int(y - self.robot_size // 2)
            painter.drawRect(QRect(top_left_x, top_left_y, self.robot_size, self.robot_size))
            
            # Draw robot number
            painter.drawText(QRect(top_left_x, top_left_y, self.robot_size, self.robot_size), 
                            Qt.AlignCenter, str(i + 1))

        self.image_label.setPixmap(self.pixmap)

    def clear_points(self):
        self.coordinates = np.empty((0, 2), dtype=int)
        self.handles = []
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        self.image_label.setPixmap(self.pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())