from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt

class WatsonResponseDialog(QDialog):
    def __init__(self, response, current_state, parent=None):
        super(WatsonResponseDialog, self).__init__(parent)
        self.response = response
        self.current_state = current_state
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Watson Response')
        layout = QVBoxLayout()

        # Watson response
        response_label = QLabel('Suggested response: ')
        self.response_edit = QTextEdit(self.response)
        layout.addWidget(response_label)
        layout.addWidget(self.response_edit)

        # Robot states
        states_label = QLabel('Robot state: ')
        layout.addWidget(states_label)

        states_layout = QHBoxLayout()
        self.state_buttons = {}
        states = ['Attention', 'Hello', 'No', 'Yes', 'Angry', 'Sad', 'Joy', 'Blush']
        for state in states:
            button = QPushButton(state)
            button.setCheckable(True)
            button.clicked.connect(self.update_state)
            states_layout.addWidget(button)
            self.state_buttons[state] = button

        layout.addLayout(states_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        send_button = QPushButton('Send')
        send_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(send_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Stabish the current state
        if self.current_state in self.state_buttons:
            self.state_buttons[self.current_state].setChecked(True)
        else:
            self.state_buttons['Attention'].setChecked(True)

    def update_state(self):
        # Unmark all other buttons
        for button in self.state_buttons.values():
            if button != self.sender():
                button.setChecked(False)

    def get_response(self):
        return self.response_edit.toPlainText()

    def get_state(self):
        for state, button in self.state_buttons.items():
            if button.isChecked():
                return state
        return 'Attention'