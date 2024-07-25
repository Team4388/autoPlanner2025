import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QRect

class ButtonEditor(QMainWindow):
    def __init__(self, pathPlanner):
        super().__init__()
        self.setWindowTitle("Button Editor")
        self.pathPlanner = pathPlanner

        self.imageLabel = QLabel(self)
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        imagePath = os.path.join(scriptDir, "images", "Field.png")
        self.pixmap = QPixmap(imagePath)
        
        if self.pixmap.isNull():
            self.imageLabel.setText(f"Image not found at: {imagePath}")
        else:
            self.imageLabel.setPixmap(self.pixmap)

        self.pathPlannerButton = QPushButton("Main Window")
        self.pathPlannerButton.clicked.connect(self.showPathPlanner)
        self.buttonEditorButton = QPushButton("Button Editor")
        self.buttonEditorButton.clicked.connect(self.showButtonEditor)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.pathPlannerButton)
        buttonLayout.addWidget(self.buttonEditorButton)

        layout = QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addWidget(self.imageLabel)

        self.timeLabel = QLabel("(0:00 / 0:15 sec)", self)
        layout.addWidget(self.timeLabel, alignment=Qt.AlignCenter)

        self.rectanglesWidget = QWidget()
        self.rectanglesLayout = QHBoxLayout()
        self.rectanglesLayout.setSpacing(0)
        self.rectanglesLayout.setContentsMargins(40, 0, 0, 0)  
        self.rectanglesWidget.setLayout(self.rectanglesLayout)
        layout.addWidget(self.rectanglesWidget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 250) 

        # Variables
        self.matchLength = 15
        self.TPS = 50
        self.matchTicks = self.matchLength * self.TPS
        self.displayTickResolution = 6.25
        self.displayTicks = round(self.matchTicks / self.displayTickResolution)

        self.currentFrame = 1
        self.keyFrameData = [{"isNode": False, "isButton": False} for _ in range(self.displayTicks)]
        self.updateKeyFrameData()
        self.displayFrames = list(range(1, self.displayTicks + 1))

        self.currentTime = [i * self.matchLength / (self.displayTicks - 1) for i in range(self.displayTicks)]
        
        num_nodes = 2
        node_indices = np.linspace(0, self.displayTicks - 1, num_nodes, dtype=int)
        for idx in node_indices:
            self.keyFrameData[idx]["isNode"] = True

        self.setupFrames()
        self.updateRectangles()
        self.updateTimeLabel()

    def updateKeyFrameData(self):
        num_nodes = len(self.pathPlanner.coordinates) if self.pathPlanner else 0
        self.keyFrameData = [{"isNode": False, "isButton": False} for _ in range(self.displayTicks)]
        
        if num_nodes > 0:
            node_indices = np.linspace(0, self.displayTicks - 1, num_nodes, dtype=int)
            for idx in node_indices:
                self.keyFrameData[idx]["isNode"] = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateRectangles()
        self.updateTimeLabel()

    def setupFrames(self):
        self.displayFrames = list(range(1, self.displayTicks + 1))
        print(len(self.keyFrameData))
        print(len(self.displayFrames))

    def showButtonEditor(self):
        self.show()
        if self.pathPlanner:
            self.pathPlanner.hide()

    def showPathPlanner(self):
        self.hide()
        if self.pathPlanner:
            self.pathPlanner.show()

    def updateScene(self):
        self.updateKeyFrameData()
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)

        if self.pathPlanner and hasattr(self.pathPlanner, 'coordinates'):
            for i, (x, y) in enumerate(self.pathPlanner.coordinates):
                nodeRect = QRect(x - self.pathPlanner.nodeSize // 6, y - self.pathPlanner.nodeSize // 6,
                                self.pathPlanner.nodeSize // 3, self.pathPlanner.nodeSize // 3)
                painter.drawEllipse(nodeRect)
                painter.drawText(nodeRect, Qt.AlignCenter, str(i + 1))

            if len(self.pathPlanner.coordinates) > 1:
                total_points = 60
                points_per_curve = total_points // len(self.pathPlanner.controlPoints)
                remaining_points = total_points % len(self.pathPlanner.controlPoints)

                for i, controlPair in enumerate(self.pathPlanner.controlPoints):
                    if i < len(self.pathPlanner.coordinates) - 1:
                        start = QPoint(self.pathPlanner.coordinates[i][0], self.pathPlanner.coordinates[i][1])
                        end = QPoint(self.pathPlanner.coordinates[i + 1][0], self.pathPlanner.coordinates[i + 1][1])
                        
                        pen = QPen(Qt.yellow if self.keyFrameData[i]["isNode"] else Qt.white)  # Set color based on isNode
                        pen.setWidth(2)
                        painter.setPen(pen)

                        num_points = points_per_curve
                        if i < remaining_points:
                            num_points += 1

                        for t in np.linspace(0, 1, num_points):
                            point = self.pointOnBezierCurve(start, controlPair[0], controlPair[1], end, t)
                            painter.drawEllipse(point, 2, 2)

                        if i == self.currentFrame - 1:
                            t = (self.currentFrame - 1) / (num_points - 1)
                            point = self.pointOnBezierCurve(start, controlPair[0], controlPair[1], end, t)
                            start_angle = self.pathPlanner.nodeAngles[i] if i < len(self.pathPlanner.nodeAngles) else 0
                            end_angle = self.pathPlanner.nodeAngles[i + 1] if i + 1 < len(self.pathPlanner.nodeAngles) else 0
                            angle = self.interpolateAngle(start_angle, end_angle, t)
                            self.drawRobot(painter, point, angle)

        painter.end()
        self.imageLabel.setPixmap(self.pixmap)
        self.updateRectangles()

    def interpolateAngle(self, start_angle, end_angle, t):
        diff = (end_angle - start_angle + 180) % 360 - 180
        return start_angle + diff * t

    def drawRobot(self, painter, position, angle):
        side_length = self.pathPlanner.nodeSize
        half_side = side_length / 2

        painter.save()
        painter.translate(position)
        painter.rotate(angle - 90)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(127, 127, 127), 2))
        painter.drawRect(-half_side, -half_side, side_length, side_length)

        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(0, 0, half_side, 0)
        painter.drawLine(half_side, 0, half_side - 5, -5)
        painter.drawLine(half_side, 0, half_side - 5, 5)

        painter.restore()

    def pointOnBezierCurve(self, start, control1, control2, end, t):
        x = (1-t)**3 * start.x() + 3*(1-t)**2*t * control1.x() + 3*(1-t)*t**2 * control2.x() + t**3 * end.x()
        y = (1-t)**3 * start.y() + 3*(1-t)**2*t * control1.y() + 3*(1-t)*t**2 * control2.y() + t**3 * end.y()
        return QPoint(int(x), int(y))

    def updateRectangles(self):
        for i in reversed(range(self.rectanglesLayout.count())):
            widgetToRemove = self.rectanglesLayout.itemAt(i).widget()
            self.rectanglesLayout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)
        
        window_width = self.rectanglesWidget.width()
        if self.keyFrameData:
            rect_width = window_width / len(self.keyFrameData) 
        
        rect_height = 100
        for index, frame in enumerate(self.keyFrameData):
            rectWidget = QWidget()
            rectWidget.setFixedSize(rect_width, rect_height)
            
            if frame["isNode"]:
                rectWidget.setStyleSheet("background-color: yellow;")
            else:
                if index % 2 == 0:
                    rectWidget.setStyleSheet("background-color: #ADD8E6;")
                else:
                    rectWidget.setStyleSheet("background-color: #00008B;")
            
            rectWidget.mousePressEvent = lambda event, idx=index: self.rectangleClicked(idx)
            self.rectanglesLayout.addWidget(rectWidget)

    def rectangleClicked(self, index):
        self.currentFrame = index + 1
        self.updateRectangles()
        self.updateScene()
        self.updateTimeLabel()

        clicked_widget = self.rectanglesLayout.itemAt(index).widget()
        clicked_widget.setStyleSheet("background-color: red;")

    def updateTimeLabel(self):
        current_time = self.currentTime[self.currentFrame - 1]
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        milliseconds = int((current_time % 1) * 1000)
        self.timeLabel.setText(f"{minutes}:{seconds:02d}.{milliseconds:03d} / {self.matchLength:.3f} sec")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ButtonEditor(None)
    window.updateScene()
    window.updateRectangles()
    window.show()
    sys.exit(app.exec())
