from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QPixmap

class PetView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.image = QPixmap("src/experience/static/Panther.png")

        self.label = QLabel()
        self.label.setPixmap(self.image)  
        self.layout.addWidget(self.label)




        
