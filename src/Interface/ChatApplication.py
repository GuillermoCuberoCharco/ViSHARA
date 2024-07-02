import os
import sys
import threading
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ibm'))
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from ibm_assistance import assistant, assistant_id, session_id, get_watson_response



class ChatApplication(QWidget):
    def __init__(self, parent=None):
        super(ChatApplication, self).__init__(parent)
        self.create_widgets()

        threading.Thread(target=self.start_wscat, daemon=True).start()

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
        wscat_path = "wscat"
        self.process = subprocess.Popen([wscat_path, "-c", "ws://localhost:8081"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)

        for line in iter(self.process.stdout.readline, ''):
            self.chat_display.append(line.strip())

            response, user_defined_contex, mood = get_watson_response(
                line.strip(), assistant, assistant_id, session_id)
            if response:
                watson_text = response['output']['generic'][0]['text']
                emotion_analysis = user_defined_contex.get('emotion', {})
                
                self.send_message(watson_text)
                self.display_message(f"Emotion: {emotion_analysis}")
                self.display_message(f"Mood: {mood}")
            else:
                self.display_message("WATSON: No response")

    def send_message(self, message):
        if message.strip() != "":
            self.display_message("SHARA: " + message)
            message += "\n"
            self.process.stdin.write(message)
            self.process.stdin.flush()
            self.message_input.clear()

    def display_message(self, message):
        self.chat_display.append(message)
