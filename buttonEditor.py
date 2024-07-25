import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QRect

'''
This window is the button editor
The button editor takes the path that is made in the path planner and lets the user fine tune the auto by adding button inputs, changing timing, etc...
'''

class ButtonEditor(QMainWindow):
    def __init__(self, pathPlanner):
        super().__init__()
        # Initialization
        self.setWindowTitle("Button Editor")
        self.pathPlanner = pathPlanner

        # Background / Field setup
        self.imageLabel = QLabel(self)
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        imagePath = os.path.join(scriptDir, "images", "Field.png")
        self.pixmap = QPixmap(imagePath)
        
        if self.pixmap.isNull():
            self.imageLabel.setText(f"Image not found at: {imagePath}")
        else:
            self.imageLabel.setPixmap(self.pixmap)

        # Buttons at the top of the screen
        self.pathPlannerButton = QPushButton("Main Window")
        self.pathPlannerButton.clicked.connect(self.showPathPlanner)
        self.buttonEditorButton = QPushButton("Button Editor")
        self.buttonEditorButton.clicked.connect(self.showButtonEditor)

        # Button layouts
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.pathPlannerButton)
        buttonLayout.addWidget(self.buttonEditorButton)

        # Adding the button layout to the main layout
        layout = QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addWidget(self.imageLabel)

        # Adding the time text to the layout
        self.timeLabel = QLabel("(0:00 / 0:15 sec)", self)
        layout.addWidget(self.timeLabel, alignment=Qt.AlignCenter)

        # Defining the overall layout
        self.rectanglesWidget = QWidget()
        self.rectanglesLayout = QHBoxLayout()
        self.rectanglesLayout.setSpacing(0)
        self.rectanglesLayout.setContentsMargins(40, 0, 0, 0)  
        self.rectanglesWidget.setLayout(self.rectanglesLayout)
        layout.addWidget(self.rectanglesWidget)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Resize the window to all of the layouts and widgets added
        self.resize(self.pixmap.width(), self.pixmap.height() + 250) 

        # Variables
        self.matchLength = 15 # How many seconds the auto lasts (it's always 15)
        self.TPS = 50 # Ticks per second (the robot runs at 50 tps)
        self.matchTicks = self.matchLength * self.TPS # The amount of ticks in a match
        self.displayTickResolution = 6.25 # The number of ticks to divide the match ticks by
        self.displayTicks = round(self.matchTicks / self.displayTickResolution) # How many ticks to show the user

        self.currentFrame = 1 # The frame that is currently selected
        self.keyFrameData = [{"isNode": False, "isButton": False} for _ in range(self.displayTicks)] # Dictionary for every tick including if that tick is a node frame or a button frame
        self.updateKeyFrameData()
        self.displayFrames = list(range(1, self.displayTicks + 1)) # The list of display frames

        self.currentTime = [i * self.matchLength / (self.displayTicks - 1) for i in range(self.displayTicks)] # Divides the amount of frames by the match length to put a time for every frame
        
        # Setting up the nodes from the path planner
        num_nodes = 2 # The number of nodes in the path planner
        node_indices = np.linspace(0, self.displayTicks - 1, num_nodes, dtype=int)
        for idx in node_indices:
            self.keyFrameData[idx]["isNode"] = True

        # Initialization
        self.setupFrames()
        self.updateRectangles()
        self.updateTimeLabel()

    # Updating the key frames with data from the path planner
    def updateKeyFrameData(self):
        num_nodes = len(self.pathPlanner.coordinates) if self.pathPlanner else 0
        self.keyFrameData = [{"isNode": False, "isButton": False} for _ in range(self.displayTicks)]
        
        if num_nodes > 0:
            node_indices = np.linspace(0, self.displayTicks - 1, num_nodes, dtype=int)
            for idx in node_indices:
                self.keyFrameData[idx]["isNode"] = True

    # Resizing the rectangles and updating the time on call
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateRectangles()
        self.updateTimeLabel()

    # Setup for the display frames
    def setupFrames(self):
        self.displayFrames = list(range(1, self.displayTicks + 1))

    # Move to the button editor window
    def showButtonEditor(self):
        self.show()
        if self.pathPlanner:
            self.pathPlanner.hide()

    # Move to the path planner window
    def showPathPlanner(self):
        self.hide()
        if self.pathPlanner:
            self.pathPlanner.show()

    # Updates the scene with all of the data from the path planner and draw the scene
    def updateScene(self):
        self.updateKeyFrameData() # Make sure key frame data is up to date

        # Draw the field
        self.pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "Field.png"))
        painter = QPainter(self.pixmap)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)

        # Draw the nodes from the path planner onto the button editor
        if self.pathPlanner and hasattr(self.pathPlanner, 'coordinates'):
            for i, (x, y) in enumerate(self.pathPlanner.coordinates):
                nodeRect = QRect(x - self.pathPlanner.nodeSize // 6, y - self.pathPlanner.nodeSize // 6,
                                self.pathPlanner.nodeSize // 3, self.pathPlanner.nodeSize // 3)
                painter.drawEllipse(nodeRect)
                painter.drawText(nodeRect, Qt.AlignCenter, str(i + 1))

            # Draw points on the bezier curve in between the nodes (Where the robot is going to go)
            if len(self.pathPlanner.coordinates) > 1:
                total_points = 60 # The amount of points to draw
                points_per_curve = total_points // len(self.pathPlanner.controlPoints)
                remaining_points = total_points % len(self.pathPlanner.controlPoints)

                # Placing the points and nodes
                for i, controlPair in enumerate(self.pathPlanner.controlPoints):
                    if i < len(self.pathPlanner.coordinates) - 1:
                        start = QPoint(self.pathPlanner.coordinates[i][0], self.pathPlanner.coordinates[i][1])
                        end = QPoint(self.pathPlanner.coordinates[i + 1][0], self.pathPlanner.coordinates[i + 1][1])
                        
                        pen = QPen(Qt.yellow if self.keyFrameData[i]["isNode"] else Qt.white)
                        pen.setWidth(2)
                        painter.setPen(pen)

                        num_points = points_per_curve
                        if i < remaining_points:
                            num_points += 1

                        # Set up the points on the bezier curve
                        for t in np.linspace(0, 1, num_points):
                            point = self.pointOnBezierCurve(start, controlPair[0], controlPair[1], end, t)
                            painter.drawEllipse(point, 2, 2)

                        # Draw every point on the bezier curve with the rotation of the robot at that point
                        if i == self.currentFrame - 1:
                            t = (self.currentFrame - 1) / (num_points - 1)
                            point = self.pointOnBezierCurve(start, controlPair[0], controlPair[1], end, t)
                            start_angle = self.pathPlanner.nodeAngles[i] if i < len(self.pathPlanner.nodeAngles) else 0
                            end_angle = self.pathPlanner.nodeAngles[i + 1] if i + 1 < len(self.pathPlanner.nodeAngles) else 0
                            angle = self.interpolateAngle(start_angle, end_angle, t)
                            self.drawRobot(painter, point, angle)

        painter.end() # If you don't end the painter the app crashes
        self.imageLabel.setPixmap(self.pixmap)
        self.updateRectangles()

    # Finds the angle between two angles
    # This is used to find the angles of all of the points in between the nodes
    def interpolateAngle(self, start_angle, end_angle, t):
        diff = (end_angle - start_angle + 180) % 360 - 180
        return start_angle + diff * t

    # Draw where the robot is at the current frame
    # DOES NOT WORK AT THE MOMENT
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

    # Function for drawing the points on the bezier curve (I dont get the math tbh)
    def pointOnBezierCurve(self, start, control1, control2, end, t):
        x = (1-t)**3 * start.x() + 3*(1-t)**2*t * control1.x() + 3*(1-t)*t**2 * control2.x() + t**3 * end.x()
        y = (1-t)**3 * start.y() + 3*(1-t)**2*t * control1.y() + 3*(1-t)*t**2 * control2.y() + t**3 * end.y()
        return QPoint(int(x), int(y))

    # Update the frames on the bottom of the screen that the user interacts with
    def updateRectangles(self):
        # Add the key frame widget
        for i in reversed(range(self.rectanglesLayout.count())):
            widgetToRemove = self.rectanglesLayout.itemAt(i).widget()
            self.rectanglesLayout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)
        
        #Set the key frames width
        window_width = self.rectanglesWidget.width()
        if self.keyFrameData:
            rect_width = window_width / len(self.keyFrameData) 
        
        rect_height = 100 # Adjustable key frame height
        for index, frame in enumerate(self.keyFrameData):
            rectWidget = QWidget()
            rectWidget.setFixedSize(rect_width, rect_height)
            
            # Set the colors of the frames
            if frame["isNode"]:
                rectWidget.setStyleSheet("background-color: yellow;")
            else:
                if index % 2 == 0:
                    rectWidget.setStyleSheet("background-color: #ADD8E6;")
                else:
                    rectWidget.setStyleSheet("background-color: #00008B;")
            
            rectWidget.mousePressEvent = lambda event, idx=index: self.rectangleClicked(idx)
            self.rectanglesLayout.addWidget(rectWidget)

    # Set the current frame to the frame that the user clicked
    def rectangleClicked(self, index):
        self.currentFrame = index + 1 # Setting the frame
        self.updateRectangles()
        self.updateScene()
        self.updateTimeLabel()

        # Set the current frame to be red
        clicked_widget = self.rectanglesLayout.itemAt(index).widget()
        clicked_widget.setStyleSheet("background-color: red;")

    # Update the time depending on the current frame
    def updateTimeLabel(self):
        current_time = self.currentTime[self.currentFrame - 1] # Sets the time to the current time
        minutes = int(current_time // 60) 
        seconds = int(current_time % 60)
        milliseconds = int((current_time % 1) * 1000)
        self.timeLabel.setText(f"{minutes}:{seconds:02d}.{milliseconds:03d} / {self.matchLength:.3f} sec")

# App initialization
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ButtonEditor(None)
    window.updateScene()
    window.updateRectangles()
    window.show()
    sys.exit(app.exec())
