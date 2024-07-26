import sys
import os
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class AboutWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setGeometry(100, 100, 700, 700)

        # Create a central widget and set the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Create a widget to hold the content
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)

        # Read the README file
        readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
        try:
            with open(readme_path, 'r') as file:
                readme_content = file.read()
        except FileNotFoundError:
            readme_content = "README.md file not found."

        about_label = QLabel(readme_content)
        about_label.setWordWrap(True)
        about_label.setTextFormat(Qt.MarkdownText)
        content_layout.addWidget(about_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = AboutWindow()
    main_window.show()
    sys.exit(app.exec())