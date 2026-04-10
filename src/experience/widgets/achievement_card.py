from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout

class Achievement_Card(QFrame):
    def __init__(self, name: str, description: str, progress: int, goal: int, unlocked: bool):
        super().__init__()
        self.setObjectName("achievementCard")

        # Set up layout
        card_layout = QHBoxLayout()
        self.setLayout(card_layout)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(4)
        self.setMinimumHeight(50)

        left = QVBoxLayout()
        left.addWidget(QLabel(name))
        left.addWidget(QLabel(description))

        card_layout.addLayout(left)
        card_layout.addWidget(QLabel(f"{progress} / {goal}"))

        # Turns background green if goal is meet
        if unlocked:
            self.setStyleSheet("""
                QFrame { background-color: #2ecc71; border-radius: 8px; }
                QFrame QLabel { color: white; background: transparent; }
            """)
        else:
            self.setStyleSheet("""
                QFrame { background-color: #2c2c2c; border-radius: 8px; }
                QFrame QLabel { color: white; background: transparent; }
            """)