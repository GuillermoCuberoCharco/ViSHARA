from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit

class WatsonResponseDialog(QDialog):
    def __init__(self, watson_response, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Watson Response")
        self.layout = QVBoxLayout()

        self.response_text = QTextEdit(watson_response)
        self.layout.addWidget(self.response_text)

        button_layout = QHBoxLayout()
        self.approve_button = QPushButton("Approve")
        button_layout.addWidget(self.approve_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.approve_button.clicked.connect(self.accept)

    def get_response(self):
        return self.response_text.toPlainText()