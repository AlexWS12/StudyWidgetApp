from PySide6.QtWidgets import QWidget, QVBoxLayout
from src.experience.widgets.centered_label import CenteredLabel

class Settings(QWidget):
    def __init__(self, parent: None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(CenteredLabel("Settings"))