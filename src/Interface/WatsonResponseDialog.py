from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit

class WatsonResponseDialog(QDialog):
    def __init__(self, watson_response, current_state, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Watson Response")
        self.layout = QVBoxLayout()

        # Response text area
        self.response_text = QTextEdit(watson_response)
        self.layout.addWidget(QLabel("Watson Response:"))
        self.layout.addWidget(self.response_text)

        # Robot state/animation input
        self.state_input = QLineEdit(current_state)
        self.layout.addWidget(QLabel("Robot State:"))
        self.layout.addWidget(self.state_input)

        button_layout = QHBoxLayout()
        self.approve_button = QPushButton("Approve")
        button_layout.addWidget(self.approve_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.approve_button.clicked.connect(self.accept)

    def get_response(self):
        return self.response_text.toPlainText()
    
    def get_state(self):
        return self.state_input.text()