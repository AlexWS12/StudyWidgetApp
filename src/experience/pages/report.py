from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from src.core.qApplication import QApplication

class report(QWidget):
    def __init__(self, parent: None):
        super().__init__(parent)

        self.app = QApplication.instance()
        self.data = self.app.database_reader.load_report_data()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(QLabel("Report"))