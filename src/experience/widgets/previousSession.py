from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class previousSession(QWidget, parent):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel(f"Score:{parent.data['user_info']['previous_session_score']}"))
        self.layout.addWidget(QLabel(f"Focused percentage: {parent.data['user_info']['previous_session_focused_percentage']}"))
        self.layout.addWidget(QLabel(f"Number of Sessions:{parent.data['user_info']['previous_session_number_of_sessions']}"))