from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from src.experience.sideBar import Sidebar
from src.experience.pages.dashboard import dashboard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Tracker Partner")

        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Main container for the main window
        self.main_container = QWidget()
        self.main_container.setLayout(QHBoxLayout())

        self.sidebar = Sidebar(self)
        self.main_container.layout().addWidget(self.sidebar)

        self.dashboard = dashboard(self)
        self.main_container.layout().addWidget(self.dashboard)

        self.setCentralWidget(self.main_container)
        self.show()

