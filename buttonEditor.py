import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QPen
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

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.scrollArea)

        self.rectanglesWidget = QWidget()
        self.scrollArea.setWidget(self.rectanglesWidget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 200)

        # VariablesssszczadasdadawsadsaaDSdasas
        self.matchLength = 15
        self.TPS = 50
        self.matchTicks = self.matchLength * self.TPS
        self.displayTickResolution = 18
        self.displayTicks = round(self.matchTicks / self.displayTickResolution)

        self.keyFrames = []
        self.displayFrames = []

        self.setupFrames()

    def setupFrames(self):
        self.keyFrames = list(range(1, self.matchTicks + 1))
        self.displayFrames = list(range(1, self.displayTicks + 1))

        print(len(self.keyFrames))
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

                angle = self.pathPlanner.nodeAngles[i] if i < len(self.pathPlanner.nodeAngles) else 0
                self.drawRobot(painter, QPoint(x, y), angle)

            if len(self.pathPlanner.coordinates) > 1:
                for i in range(len(self.pathPlanner.coordinates) - 1):
                    start = QPoint(self.pathPlanner.coordinates[i][0], self.pathPlanner.coordinates[i][1])
                    end = QPoint(self.pathPlanner.coordinates[i + 1][0], self.pathPlanner.coordinates[i + 1][1])

                    if i < len(self.pathPlanner.controlPoints):
                        controlPair = self.pathPlanner.controlPoints[i]

                        start_angle = self.pathPlanner.nodeAngles[i] if i < len(self.pathPlanner.nodeAngles) else 0
                        end_angle = self.pathPlanner.nodeAngles[i + 1] if i + 1 < len(self.pathPlanner.nodeAngles) else 0

                        for t in np.linspace(0, 1, self.displayTicks)[1:-1]:
                            point = self.pointOnBezierCurve(start, controlPair[0], controlPair[1], end, t)
                            current_angle = self.interpolateAngle(start_angle, end_angle, t)
                            self.drawRobot(painter, point, current_angle)

        painter.end()
        self.imageLabel.setPixmap(self.pixmap)

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
        if self.rectanglesWidget.layout():
            QWidget().setLayout(self.rectanglesWidget.layout())
        
        layout = QHBoxLayout()
        layout.setSpacing(2)
        
        rect_width = 20
        rect_height = 50
        
        for frame in self.displayFrames:
            rectWidget = QWidget()
            rectWidget.setFixedSize(rect_width, rect_height)
            rectWidget.setAutoFillBackground(True)
            rectWidget.setStyleSheet("background-color: white; border: 1px solid black;")

            layout.addWidget(rectWidget)

        self.rectanglesWidget.setLayout(layout)
        self.rectanglesWidget.setFixedHeight(rect_height + 10)
        self.rectanglesWidget.setMinimumWidth(len(self.displayFrames) * (rect_width + 2))

        self.scrollArea.setWidget(self.rectanglesWidget)
        self.scrollArea.setFixedHeight(rect_height + 30)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ButtonEditor(None)
    window.updateScene()
    window.show()
    sys.exit(app.exec())