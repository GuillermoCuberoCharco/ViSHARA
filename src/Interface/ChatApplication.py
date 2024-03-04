from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
import subprocess
import threading


class ChatApplication(QWidget):
    def __init__(self, parent=None):
        super(ChatApplication, self).__init__(parent)
        self.create_widgets()

        self.event_service_process = subprocess.Popen(
            "node src/service/EventService.cjs")

        threading.Thread(target=self.start_wscat, daemon=True).start()

        self.predefined_responses = [
            "/Holi!!", "/Hola, ¿cómo estás?", "/¿En qué puedo ayudarte?"]
        self.predefined_response_buttons = []

    def quit(self):
        self.event_service_process.terminate()
        super().quit()

    def create_widgets(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(
            lambda: self.send_message(self.message_input.text()))
        self.layout.addWidget(self.message_input)

        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(
            lambda: self.send_message(self.message_input.text()))
        self.layout.addWidget(self.send_button)

    def start_wscat(self):
        wscat_path = "C:/Users/Usuario/AppData/Roaming/npm/wscat.cmd"
        self.process = subprocess.Popen([wscat_path, "-c", "ws://localhost:8081"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)

        for line in iter(self.process.stdout.readline, ''):
            self.chat_display.append(line.strip())

            if not self.predefined_response_buttons:
                self.display_predefined_response()

    def display_predefined_response(self):
        for response in self.predefined_responses:
            button = QPushButton(response)
            button.clicked.connect(
                lambda response=response: self.send_predefined_response(response))
            self.layout.addWidget(button)
            self.predefined_response_buttons.append(button)

    def send_predefined_response(self, response):
        self.send_message(response)
        for button in self.predefined_response_buttons:
            button.deleteLater()
        self.predefined_response_buttons = []

    def send_message(self, message):
        if message.strip() != "":
            self.display_message("SHARA: " + message)
            message += "\n"
            self.process.stdin.write(message)
            self.process.stdin.flush()
            self.message_input.clear()

    def display_message(self, message):
        self.chat_display.append(message)
