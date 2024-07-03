import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QPainterPath, QPolygon, QFont
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

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 60)

        # Variables
        self.matchLength = 15
        self.TPS = 50
        self.matchTicks = self.matchLength * self.TPS
        self.displayTickResolution = 4
        self.displayTicks = round(self.matchTicks / self.displayTickResolution)

        self.keyFrames = []

    def addKeyFrames(self):
        currentFrame = 0

        for i in range(0, self.displayTicks):
            self.keyFrames.append(currentFrame)            

    def showButtonEditor(self):
        self.show()
        self.pathPlanner.hide()

    def showPathPlanner(self):
        self.hide()
        self.pathPlanner.show()

    def updateScene(self):
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        greyPen = QPen(QColor(127, 127, 127))
        greyPen.setWidth(2)
        painter.setPen(greyPen)

        # Draw the Bezier curve segments
        if self.pathPlanner.coordinates.size > 0:
            for i in range(len(self.pathPlanner.coordinates) - 1):
                start = QPoint(self.pathPlanner.coordinates[i][0], self.pathPlanner.coordinates[i][1])
                end = QPoint(self.pathPlanner.coordinates[i + 1][0], self.pathPlanner.coordinates[i + 1][1])

                if i < len(self.pathPlanner.controlPoints):
                    controlPair = self.pathPlanner.controlPoints[i]

                    pen = QPen(Qt.yellow)
                    pen.setWidth(2)
                    painter.setPen(pen)

                    path = QPainterPath()
                    path.moveTo(start)
                    path.cubicTo(controlPair[0], controlPair[1], end)
                    painter.drawPath(path)

        # Draw the nodes
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSize(25)
        painter.setFont(font)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)

        for i, (x, y) in enumerate(self.pathPlanner.coordinates):
            nodeRect = QRect(x - self.pathPlanner.nodeSize // 6, y - self.pathPlanner.nodeSize // 6,
                            self.pathPlanner.nodeSize // 3, self.pathPlanner.nodeSize // 3)
            painter.drawEllipse(nodeRect)
            painter.drawText(nodeRect, Qt.AlignCenter, str(i + 1))

        painter.end()
        self.imageLabel.setPixmap(self.pixmap)
