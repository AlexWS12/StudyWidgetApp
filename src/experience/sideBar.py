from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from src.experience.button import Button

from typing import TYPE_CHECKING # avoid circular imports

if TYPE_CHECKING: 
    from src.experience.mainWindow import MainWindow

class Sidebar(QWidget):
    def __init__(self, main_window : MainWindow):
        super().__init__()
        self.main_window = main_window

        # layout for sidebar
        self.layout = QVBoxLayout() 
        self.setLayout(self.layout)

        self.add_buttons()

        # Adds widget to sidebar
    def add_items(self, widget: QWidget):
        self.layout.addWidget(widget)

        # Adds all the navigation buttons to sidebar
    def add_buttons(self):
        self.add_items(QLabel("Sidebar"))
        self.add_items(Button("Dashboard"))
        self.add_items(Button("Session"))
        self.add_items(Button("Report"))
        self.add_items(Button("Virtual Pet"))
        self.add_items(Button("Achievement"))

