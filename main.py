import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QPainterPath, QPolygon, QFont
from PySide6.QtCore import Qt, QPoint, QRect

from buttonEditor import ButtonEditor

class PathPlanner(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Auto Planner")

        self.coordinates = np.empty((0, 2), dtype=int)
        self.control_points = []
        self.rotation_handles = []
        self.node_angles = []

        self.image_label = QLabel(self)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "Field.png")
        self.pixmap = QPixmap(image_path)
        
        if self.pixmap.isNull():
            self.image_label.setText(f"Image not found at: {image_path}")
        else:
            self.image_label.setPixmap(self.pixmap)

        self.main_window_button = QPushButton("Main Window")
        self.main_window_button.clicked.connect(self.show_main_window)
        self.button_editor_button = QPushButton("Button Editor")
        self.button_editor_button.clicked.connect(self.show_button_editor)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.main_window_button)
        button_layout.addWidget(self.button_editor_button)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.image_label)

        self.button_editor = ButtonEditor(self)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 60)

        self.setMouseTracking(True)

        self.last_click_pos = QPoint()

        self.coordinates = np.empty((0, 2), dtype=int)
        self.last_click_time = 0
        self.node_size = 35
        self.handle_size = 15
        self.rotation_handle_distance = 35
        self.control_points = []
        self.rotation_handles = []
        self.node_angles = []
        self.dragging_control_point = False
        self.dragging_node = False
        self.dragging_rotation_handle = False
        self.dragging_control_point_index = (-1, -1)
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
                    self.calculate_control_points()
                self.calculate_rotation_handle_pos()
                self.draw_scene()
                self.button_editor.update_scene()
            elif event.button() == Qt.LeftButton:
                current_time = event.timestamp()
                if (current_time - self.last_click_time < 300 and 
                    (pos - self.last_click_pos).manhattanLength() < 5):
                    node_index = self.is_point_in_node(x, y)
                    if node_index != -1:
                        self.delete_node(node_index)
                    else:
                        control_point_index = self.is_point_in_control_point(x, y)
                        if control_point_index != (-1, -1):
                            self.smoothPoints(control_point_index[0], control_point_index[1])
                            self.draw_scene()
                            self.button_editor.update_scene()
                else:
                    control_point_index = self.is_point_in_control_point(x, y)
                    if control_point_index != (-1, -1):
                        self.dragging_control_point = True
                        self.dragging_control_point_index = control_point_index
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
        if index < len(self.control_points):
            del self.control_points[index]
        if index > 0 and index < len(self.control_points):
            del self.control_points[index - 1]
        if index < len(self.rotation_handles):
            del self.rotation_handles[index]
        self.draw_scene()
        self.button_editor.update_scene()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging_control_point:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            curve_index, point_index = self.dragging_control_point_index
            self.control_points[curve_index][point_index] = QPoint(x, y)
            self.draw_scene()
            self.button_editor.update_scene()
        elif self.dragging_node:
            pos = self.image_label.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            self.coordinates[self.dragging_node_index] = [x, y]
            self.calculate_control_points()
            self.calculate_rotation_handle_pos()
            self.draw_scene()
            self.button_editor.update_scene()
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
            self.button_editor.update_scene()

    #Resets dragging when mouse is released
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging_control_point = False
            self.dragging_control_point_index = (-1, -1)
            self.dragging_node = False
            self.dragging_node_index = -1
            self.dragging_rotation_handle = False
            self.dragging_rotation_handle_index = -1
            self.button_editor.update_scene()

    #These 3 are for distinguishing what the user is clicking
    def is_point_in_rotation_handle(self, x, y):
        for i, handle in enumerate(self.rotation_handles):
            if (abs(x - handle.x()) <= self.handle_size // 2 and
                abs(y - handle.y()) <= self.handle_size // 2):
                return i
        return -1

    def is_point_in_control_point(self, x, y):
        for i, control_pair in enumerate(self.control_points):
            for j, control_point in enumerate(control_pair):
                if (abs(x - control_point.x()) <= self.handle_size // 2 and
                    abs(y - control_point.y()) <= self.handle_size // 2):
                    return (i, j)
        return (-1, -1)

    def is_point_in_node(self, x, y):
        for i, (node_x, node_y) in enumerate(self.coordinates):
            if (abs(x - node_x) <= self.node_size // 2 and
                abs(y - node_y) <= self.node_size // 2):
                return i
        return -1
    
    #Calculating the handle positions
    def calculate_control_points(self):
        if len(self.coordinates) >= 2:
            x1, y1 = self.coordinates[-2]
            x2, y2 = self.coordinates[-1]
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
            self.control_points.append([
                QPoint(mid_x - (x2 - x1) // 4, mid_y - (y2 - y1) // 4),
                QPoint(mid_x + (x2 - x1) // 4, mid_y + (y2 - y1) // 4)
            ])

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

    #Updates buttonEditor
    def update_scene(self):
        self.button_editor.update_scene(self.coordinates, self.control_points)

    #Draws the scene, big important function
    def draw_scene(self):
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        grey_pen = QPen(QColor(127, 127, 127))
        grey_pen.setWidth(2)
        painter.setPen(grey_pen)
        for i, control_pair in enumerate(self.control_points):
            if i < len(self.coordinates) - 1:
                start = QPoint(self.coordinates[i][0], self.coordinates[i][1])
                end = QPoint(self.coordinates[i + 1][0], self.coordinates[i + 1][1])
                
                pen = QPen(Qt.yellow)
                pen.setWidth(2)
                painter.setPen(pen)

                path = QPainterPath()
                path.moveTo(start)
                path.cubicTo(control_pair[0], control_pair[1], end)
                painter.drawPath(path)

                painter.setBrush(Qt.NoBrush)
                for control_point in control_pair:
                    painter.setPen(QPen(QColor(127, 127, 127), 1, Qt.DashLine))
                    painter.drawLine(start, control_point)
                    painter.drawLine(end, control_point)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 255, 255))
                for control_point in control_pair:
                    painter.drawEllipse(
                        control_point.x() - self.handle_size // 2,
                        control_point.y() - self.handle_size // 2,
                        self.handle_size,
                        self.handle_size
                    )
                painter.setBrush(Qt.NoBrush)

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
                painter.drawText(QRect(x - self.node_size // 2, y - self.node_size // 2, 
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
        self.button_editor.update_scene()

    #S M O O T H
    def smoothPoints(self, curve_index: int, point_index: int):
        if curve_index + 1 < len(self.control_points):
            prev_control_pair = self.control_points[curve_index]
            next_control_pair = self.control_points[curve_index + 1]
            node = QPoint(self.coordinates[curve_index + 1][0], self.coordinates[curve_index + 1][1])

            #Calculate the new position for the second control point
            new_control2 = QPoint(
                2 * node.x() - next_control_pair[0].x(),
                2 * node.y() - next_control_pair[0].y()
            )
            self.control_points[curve_index][1] = new_control2

            #Calculate the new position for the first control point
            new_control1 = QPoint(
                2 * node.x() - prev_control_pair[1].x(),
                2 * node.y() - prev_control_pair[1].y()
            )
            self.control_points[curve_index + 1][0] = new_control1

    #Clears all
    def clear_points(self):
        self.coordinates = np.empty((0, 2), dtype=int)
        self.control_points.clear()
        self.rotation_handles.clear()
        self.node_angles.clear()
        self.draw_scene()
        self.button_editor.update_scene()

    #Warning for clearing
    def show_clear_warning(self):
        reply = QMessageBox.question(self, "Clear Auto", 
                                        "Are you sure you want to clear this auto?", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_points() 

    def show_main_window(self):
        self.show()
        self.button_editor.hide()

    def show_button_editor(self):
        self.hide()
        self.button_editor.show()            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PathPlanner()
    window.show()
    sys.exit(app.exec())