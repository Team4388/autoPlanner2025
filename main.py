import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QPainterPath, QPolygon, QFont
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
        self.last_click_pos = QPoint()

        self.coordinates = np.empty((0, 2), dtype=int)
        self.last_click_time = 0
        self.node_size = 35
        self.handle_size = 15
        self.rotation_handle_distance = 35
        self.handles = []
        self.rotation_handles = []
        self.node_angles = []
        self.dragging_handle = False
        self.dragging_node = False
        self.dragging_rotation_handle = False
        self.dragging_handle_index = -1
        self.dragging_node_index = -1
        self.dragging_rotation_handle_index = -1

    #Tells when either the left or right mouse button is pressed
    def mousePressEvent(self, event: QMouseEvent):
        pos = self.image_label.mapFrom(self, event.position().toPoint())
        x, y = pos.x(), pos.y()
        
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            if event.button() == Qt.RightButton:
                self.coordinates = np.vstack((self.coordinates, [x, y]))
                if len(self.coordinates) >= 2:
                    self.calculate_handle_pos()
                self.calculate_rotation_handle_pos()
                self.draw_scene()
                self.draw_scene()
            elif event.button() == Qt.LeftButton:
                current_time = event.timestamp()
                if (current_time - self.last_click_time < 300 and 
                    (pos - self.last_click_pos).manhattanLength() < 5):
                    node_index = self.is_point_in_node(x, y)
                    if node_index != -1:
                        self.delete_node(node_index)
                    else:
                        handle_index = self.is_point_in_handle(x, y)
                        if handle_index != -1:
                            self.smoothPoints(handle_index)
                            self.draw_scene()
                else:
                    handle_index = self.is_point_in_handle(x, y)
                    if handle_index != -1:
                        self.dragging_handle = True
                        self.dragging_handle_index = handle_index
                    else:
                        node_index = self.is_point_in_node(x, y)
                        if node_index != -1:
                            self.dragging_node = True
                            self.dragging_node_index = node_index
                        else:
                            rotation_handle_index = self.is_point_in_rotation_handle(x, y)
                            if rotation_handle_index != -1:
                                self.dragging_rotation_handle = True
                                self.dragging_rotation_handle_index = rotation_handle_index
                
                self.last_click_time = current_time
                self.last_click_pos = pos

    #Deletes node
    def delete_node(self, index):
        self.coordinates = np.delete(self.coordinates, index, axis=0)
        if index < len(self.handles):
            del self.handles[index]
        if index < len(self.rotation_handles):
            del self.rotation_handles[index]
        self.draw_scene()

    #
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging_handle:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            self.handles[self.dragging_handle_index] = QPoint(x, y)
            self.draw_scene()
        elif self.dragging_node:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            self.coordinates[self.dragging_node_index] = [x, y]
            self.calculate_handle_pos()
            self.calculate_rotation_handle_pos()
            self.draw_scene()
        elif self.dragging_rotation_handle:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            node_x, node_y = self.coordinates[self.dragging_rotation_handle_index]
            dx = x - node_x
            dy = y - node_y
            angle = np.arctan2(dy, dx)

            self.node_angles[self.dragging_rotation_handle_index] = angle

            rotation_handle_x = int(node_x + self.rotation_handle_distance * np.cos(angle))
            rotation_handle_y = int(node_y + self.rotation_handle_distance * np.sin(angle))
            self.rotation_handles[self.dragging_rotation_handle_index] = QPoint(rotation_handle_x, rotation_handle_y)
            self.draw_scene()
            self.draw_scene()

    #Resets dragging when mouse is released
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging_handle = False
            self.dragging_handle_index = -1
            self.dragging_node = False
            self.dragging_node_index = -1
            self.dragging_rotation_handle = False
            self.dragging_rotation_handle_index = -1

    #These 3 are for distinguishing what the user is clicking
    def is_point_in_rotation_handle(self, x, y):
        for i, handle in enumerate(self.rotation_handles):
            if (abs(x - handle.x()) <= self.handle_size // 2 and
                abs(y - handle.y()) <= self.handle_size // 2):
                return i
        return -1

    def is_point_in_handle(self, x, y):
        for i, handle in enumerate(self.handles):
            if (abs(x - handle.x()) <= self.handle_size // 2 and
                abs(y - handle.y()) <= self.handle_size // 2):
                return i
        return -1

    def is_point_in_node(self, x, y):
        for i, (node_x, node_y) in enumerate(self.coordinates):
            if (abs(x - node_x) <= self.node_size // 2 and
                abs(y - node_y) <= self.node_size // 2):
                return i
        return -1
    
    #Calculating the handle positions
    def calculate_handle_pos(self):
        if len(self.coordinates) >= 2:
            x1, y1 = self.coordinates[-2]
            x2, y2 = self.coordinates[-1]
            self.handles.append(QPoint((x1 + x2) // 2, (y1 + y2) // 2))

    def calculate_rotation_handle_pos(self):
        for i, (x, y) in enumerate(self.coordinates):
            if i >= len(self.node_angles):
                self.node_angles.append(np.pi)  # Default angle for new nodes
            
            angle = self.node_angles[i]
            
            rotation_handle_x = int(x + self.rotation_handle_distance * np.cos(angle))
            rotation_handle_y = int(y + self.rotation_handle_distance * np.sin(angle))
            
            if i >= len(self.rotation_handles):
                self.rotation_handles.append(QPoint(rotation_handle_x, rotation_handle_y))
            else:
                self.rotation_handles[i] = QPoint(rotation_handle_x, rotation_handle_y)  

    #Draws the scene, big important function
    def draw_scene(self):
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        grey_pen = QPen(QColor(127, 127, 127))
        grey_pen.setWidth(2)
        painter.setPen(grey_pen)
        for i, handle in enumerate(self.handles):
            if i < len(self.coordinates) and i + 1 < len(self.coordinates):
                node1_pos = QPoint(self.coordinates[i][0], self.coordinates[i][1])
                node2_pos = QPoint(self.coordinates[i+1][0], self.coordinates[i+1][1])
                painter.drawLine(handle, node1_pos)
                painter.drawLine(handle, node2_pos)
                                 
        if len(self.coordinates) >= 2:
            for i in range(len(self.coordinates) - 1):
                start = QPoint(self.coordinates[i][0], self.coordinates[i][1])
                end = QPoint(self.coordinates[i + 1][0], self.coordinates[i + 1][1])
                
                if i < len(self.handles):
                    pen = QPen(Qt.yellow)
                    pen.setWidth(2)
                    painter.setPen(pen)

                    path = QPainterPath()
                    path.moveTo(start)
                    handle = self.handles[i]
                    path.cubicTo(handle, handle, end)
                    painter.drawPath(path)

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(0, 255, 255)) 
                    painter.drawEllipse(
                        handle.x() - self.handle_size // 2,
                        handle.y() - self.handle_size // 2,
                        self.handle_size,
                        self.handle_size
                    )
                    painter.setBrush(Qt.NoBrush)
                else:
                    painter.drawLine(start, end)

        for i, (x, y) in enumerate(self.coordinates):
            if i < len(self.rotation_handles):
                angle = self.node_angles[i]
                
                painter.save()
                painter.translate(x, y)
                painter.rotate(np.degrees(angle))
                
                pen = QPen(QColor(127, 127, 127))  
                pen.setWidth(2)  
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush) 
                painter.drawRect(-self.node_size // 2, -self.node_size // 2, 
                                self.node_size, self.node_size)
                
                painter.restore()
                
                painter.setPen(Qt.white)
                font = painter.font()
                font.setPointSize(25)
                painter.setFont(font)
                painter.drawText(QRect(x - self.node_size//2, y - self.node_size//2, 
                                    self.node_size, self.node_size), 
                                Qt.AlignCenter, str(i + 1))
        
        for i, handle in enumerate(self.rotation_handles):
            painter.setBrush(QColor(255, 0, 255))
            painter.drawEllipse(
                handle,
                self.handle_size // 2,
                self.handle_size // 2
            )
            painter.setBrush(Qt.NoBrush)

        self.image_label.setPixmap(self.pixmap)

    #S M O O T H
    def smoothPoints(self, index: int):
        curveEditPoints = self.handles
        nodes = [QPoint(x, y) for x, y in self.coordinates]

        for i in range(index+1, len(curveEditPoints)):
            controlPointPos = curveEditPoints[i-1]
            nodePos = nodes[i]
            curveEditPoints[i] = QPoint(
                2*nodePos.x() - controlPointPos.x(),
                2*nodePos.y() - controlPointPos.y()
            )
        for i in range(0, index):
            controlPointPos = curveEditPoints[index-i]
            nodePos = nodes[index-i]
            curveEditPoints[index-i-1] = QPoint(
                2*nodePos.x() - controlPointPos.x(),
                2*nodePos.y() - controlPointPos.y()
            )

        self.handles = curveEditPoints

    #Clears all
    def clear_points(self):
        self.coordinates = np.empty((0, 2), dtype=int)
        self.handles = []
        self.rotation_handles = []
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        self.image_label.setPixmap(self.pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())