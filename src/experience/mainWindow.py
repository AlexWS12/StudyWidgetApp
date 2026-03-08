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
        self.layout = QHBoxLayout()
        self.main_container.setLayout(self.layout)
        self.setCentralWidget(self.main_container)

        # Initilize Sidebar
        self.sidebar = Sidebar(self)
        self.layout.addWidget(self.sidebar)

        # placeholder for main content
        self.layout.addWidget(QWidget())  

        self.show()

