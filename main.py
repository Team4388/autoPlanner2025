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
        self.controlPoints = []
        self.rotationHandles = []
        self.nodeAngles = []

        self.imageLabel = QLabel(self)

        scriptDir = os.path.dirname(os.path.abspath(__file__))
        imagePath = os.path.join(scriptDir, "images", "Field.png")
        self.pixmap = QPixmap(imagePath)
        
        if self.pixmap.isNull():
            self.imageLabel.setText(f"Image not found at: {imagePath}")
        else:
            self.imageLabel.setPixmap(self.pixmap)

        self.mainWindowButton = QPushButton("Main Window")
        self.mainWindowButton.clicked.connect(self.showMainWindow)
        self.buttonEditorButton = QPushButton("Button Editor")
        self.buttonEditorButton.clicked.connect(self.showButtonEditor)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.mainWindowButton)
        buttonLayout.addWidget(self.buttonEditorButton)

        layout = QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addWidget(self.imageLabel)

        self.buttonEditor = ButtonEditor(self)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.pixmap.width(), self.pixmap.height() + 60)

        self.setMouseTracking(True)

        self.lastClickPos = QPoint()

        self.coordinates = np.empty((0, 2), dtype=int)
        self.lastClickTime = 0
        self.nodeSize = 35
        self.handleSize = 15
        self.rotationHandleDistance = 35
        self.controlPoints = []
        self.rotationHandles = []
        self.nodeAngles = []
        self.draggingControlPoint = False
        self.draggingNode = False
        self.draggingRotationHandle = False
        self.draggingControlPointIndex = (-1, -1)
        self.draggingNodeIndex = -1
        self.draggingRotationHandleIndex = -1

    def mousePressEvent(self, event: QMouseEvent):
        pos = self.imageLabel.mapFrom(self, event.position().toPoint())
        x, y = pos.x(), pos.y()
        
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            if event.button() == Qt.RightButton:
                self.coordinates = np.vstack((self.coordinates, [x, y]))
                if len(self.coordinates) >= 2:
                    self.calculateControlPoints()
                self.calculateRotationHandlePos()
                self.drawScene()
                self.buttonEditor.updateScene()
            elif event.button() == Qt.LeftButton:
                currentTime = event.timestamp()
                if (currentTime - self.lastClickTime < 300 and 
                    (pos - self.lastClickPos).manhattanLength() < 5):
                    nodeIndex = self.isPointInNode(x, y)
                    if nodeIndex != -1:
                        self.deleteNode(nodeIndex)
                    else:
                        controlPointIndex = self.isPointInControlPoint(x, y)
                        if controlPointIndex != (-1, -1):
                            self.smoothPoints(controlPointIndex[0], controlPointIndex[1])
                            self.drawScene()
                            self.buttonEditor.updateScene()
                else:
                    controlPointIndex = self.isPointInControlPoint(x, y)
                    if controlPointIndex != (-1, -1):
                        self.draggingControlPoint = True
                        self.draggingControlPointIndex = controlPointIndex
                    else:
                        nodeIndex = self.isPointInNode(x, y)
                        if nodeIndex != -1:
                            self.draggingNode = True
                            self.draggingNodeIndex = nodeIndex
                        else:
                            rotationHandleIndex = self.isPointInRotationHandle(x, y)
                            if rotationHandleIndex != -1:
                                self.draggingRotationHandle = True
                                self.draggingRotationHandleIndex = rotationHandleIndex

                self.lastClickTime = currentTime
                self.lastClickPos = pos

    def deleteNode(self, index):
        self.coordinates = np.delete(self.coordinates, index, axis=0)
        if index < len(self.controlPoints):
            del self.controlPoints[index]
        if index > 0 and index < len(self.controlPoints):
            del self.controlPoints[index - 1]
        if index < len(self.rotationHandles):
            del self.rotationHandles[index]
        self.drawScene()
        self.buttonEditor.updateScene()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.draggingControlPoint:
            pos = self.imageLabel.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            curveIndex, pointIndex = self.draggingControlPointIndex
            self.controlPoints[curveIndex][pointIndex] = QPoint(x, y)
            self.drawScene()
            self.buttonEditor.updateScene()
        elif self.draggingNode:
            pos = self.imageLabel.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            self.coordinates[self.draggingNodeIndex] = [x, y]
            self.calculateControlPoints()
            self.calculateRotationHandlePos()
            self.drawScene()
            self.buttonEditor.updateScene()
        elif self.draggingRotationHandle:
            pos = self.imageLabel.mapFrom(self, event.position().toPoint())
            x, y = pos.x(), pos.y()
            nodeX, nodeY = self.coordinates[self.draggingRotationHandleIndex]
            dx = x - nodeX
            dy = y - nodeY
            angle = np.arctan2(dy, dx)

            self.nodeAngles[self.draggingRotationHandleIndex] = angle

            rotationHandleX = int(nodeX + self.rotationHandleDistance * np.cos(angle))
            rotationHandleY = int(nodeY + self.rotationHandleDistance * np.sin(angle))
            self.rotationHandles[self.draggingRotationHandleIndex] = QPoint(rotationHandleX, rotationHandleY)
            self.drawScene()
            self.buttonEditor.updateScene()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.draggingControlPoint = False
            self.draggingControlPointIndex = (-1, -1)
            self.draggingNode = False
            self.draggingNodeIndex = -1
            self.draggingRotationHandle = False
            self.draggingRotationHandleIndex = -1
            self.buttonEditor.updateScene()

    def isPointInRotationHandle(self, x, y):
        for i, handle in enumerate(self.rotationHandles):
            if (abs(x - handle.x()) <= self.handleSize // 2 and
                abs(y - handle.y()) <= self.handleSize // 2):
                return i
        return -1

    def isPointInControlPoint(self, x, y):
        for i, controlPair in enumerate(self.controlPoints):
            for j, controlPoint in enumerate(controlPair):
                if (abs(x - controlPoint.x()) <= self.handleSize // 2 and
                    abs(y - controlPoint.y()) <= self.handleSize // 2):
                    return (i, j)
        return (-1, -1)

    def isPointInNode(self, x, y):
        for i, (nodeX, nodeY) in enumerate(self.coordinates):
            if (abs(x - nodeX) <= self.nodeSize // 2 and
                abs(y - nodeY) <= self.nodeSize // 2):
                return i
        return -1
    
    def calculateControlPoints(self):
        if len(self.coordinates) >= 2:
            x1, y1 = self.coordinates[-2]
            x2, y2 = self.coordinates[-1]
            midX, midY = (x1 + x2) // 2, (y1 + y2) // 2
            self.controlPoints.append([
                QPoint(midX - (x2 - x1) // 4, midY - (y2 - y1) // 4),
                QPoint(midX + (x2 - x1) // 4, midY + (y2 - y1) // 4)
            ])

    def calculateRotationHandlePos(self):
        for i, (x, y) in enumerate(self.coordinates):
            if i >= len(self.nodeAngles):
                self.nodeAngles.append(np.pi)  # Default angle for new nodes
            
            angle = self.nodeAngles[i]
            
            rotationHandleX = int(x + self.rotationHandleDistance * np.cos(angle))
            rotationHandleY = int(y + self.rotationHandleDistance * np.sin(angle))
            
            if i >= len(self.rotationHandles):
                self.rotationHandles.append(QPoint(rotationHandleX, rotationHandleY))
            else:
                self.rotationHandles[i] = QPoint(rotationHandleX, rotationHandleY)  

    def updateScene(self):
        self.buttonEditor.updateScene(self.coordinates, self.controlPoints)

    def drawScene(self):
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        greyPen = QPen(QColor(127, 127, 127))
        greyPen.setWidth(2)
        painter.setPen(greyPen)
        for i, controlPair in enumerate(self.controlPoints):
            if i < len(self.coordinates) - 1:
                start = QPoint(self.coordinates[i][0], self.coordinates[i][1])
                end = QPoint(self.coordinates[i + 1][0], self.coordinates[i + 1][1])
                
                pen = QPen(Qt.yellow)
                pen.setWidth(2)
                painter.setPen(pen)

                path = QPainterPath()
                path.moveTo(start)
                path.cubicTo(controlPair[0], controlPair[1], end)
                painter.drawPath(path)

                painter.setBrush(Qt.NoBrush)
                for controlPoint in controlPair:
                    painter.setPen(QPen(QColor(127, 127, 127), 1, Qt.DashLine))
                    painter.drawLine(start, controlPoint)
                    painter.drawLine(end, controlPoint)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 255, 255))
                for controlPoint in controlPair:
                    painter.drawEllipse(
                        controlPoint.x() - self.handleSize // 2,
                        controlPoint.y() - self.handleSize // 2,
                        self.handleSize,
                        self.handleSize
                    )
                painter.setBrush(Qt.NoBrush)

        for i, (x, y) in enumerate(self.coordinates):
            if i < len(self.rotationHandles):
                angle = self.nodeAngles[i]
                
                painter.save()
                painter.translate(x, y)
                painter.rotate(np.degrees(angle))
                
                pen = QPen(QColor(127, 127, 127))  
                pen.setWidth(2)  
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush) 
                painter.drawRect(-self.nodeSize // 2, -self.nodeSize // 2, 
                                self.nodeSize, self.nodeSize)
                
                painter.restore()
                
                painter.setPen(Qt.white)
                font = painter.font()
                font.setPointSize(25)
                painter.setFont(font)
                painter.drawText(QRect(x - self.nodeSize // 2, y - self.nodeSize // 2, 
                                    self.nodeSize, self.nodeSize), 
                                Qt.AlignCenter, str(i + 1))
        
        for i, handle in enumerate(self.rotationHandles):
            painter.setBrush(QColor(255, 0, 255))
            painter.drawEllipse(
                handle,
                self.handleSize // 2,
                self.handleSize // 2
            )
            painter.setBrush(Qt.NoBrush)

        self.imageLabel.setPixmap(self.pixmap)
        self.buttonEditor.updateScene()

    def smoothPoints(self, curveIndex: int, pointIndex: int):
        if curveIndex + 1 < len(self.controlPoints):
            prevControlPair = self.controlPoints[curveIndex]
            nextControlPair = self.controlPoints[curveIndex + 1]
            node = QPoint(self.coordinates[curveIndex + 1][0], self.coordinates[curveIndex + 1][1])

            newControl2 = QPoint(
                2 * node.x() - nextControlPair[0].x(),
                2 * node.y() - nextControlPair[0].y()
            )
            self.controlPoints[curveIndex][1] = newControl2

            newControl1 = QPoint(
                2 * node.x() - prevControlPair[1].x(),
                2 * node.y() - prevControlPair[1].y()
            )
            self.controlPoints[curveIndex + 1][0] = newControl1

    def clearPoints(self):
        self.coordinates = np.empty((0, 2), dtype=int)
        self.controlPoints.clear()
        self.rotationHandles.clear()
        self.nodeAngles.clear()
        self.drawScene()
        self.buttonEditor.updateScene()

    def showClearWarning(self):
        reply = QMessageBox.question(self, "Clear Auto", 
                                        "Are you sure you want to clear this auto?", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clearPoints() 

    def showMainWindow(self):
        self.show()
        self.buttonEditor.hide()

    def showButtonEditor(self):
        self.hide()
        self.buttonEditor.show()            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PathPlanner()
    window.show()
    sys.exit(app.exec())
