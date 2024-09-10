import sys
import threading
import json
import websocket
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QDialog, QLabel
from PyQt5.QtCore import pyqtSignal, Qt

class ChatApplication(QWidget):
    watson_response_received = pyqtSignal(dict)
    def __init__(self, parent=None):
        super(ChatApplication, self).__init__(parent)
        self.create_widgets()
        self.ws = None
        self.watson_response_received.connect(self.handle_watson_response)
        threading.Thread(target=self.start_websocket, daemon=True).start()
        self.auto_mode = False

    def quit(self):
        self.event_service_process.terminate()
        super().quit()

    def create_widgets(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Message")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)

        self.state_input = QLineEdit()
        self.state_input.setPlaceholderText("Robot state")
        input_layout.addWidget(self.state_input)

        self.layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)

        self.mode_button = QPushButton('Auto mode')
        self.mode_button.clicked.connect(self.toggle_mode)
        button_layout.addWidget(self.mode_button)

        self.layout.addLayout(button_layout)

        self.mode_label = QLabel('Auto mode: OFF')
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.mode_label)

    def toggle_mode(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.mode_button.setText('Auto mode: OFF')
            self.mode_label.setText('Auto mode: ON')
            self.message_input.setEnabled(False)
            self.state_input.setEnabled(False)
            self.send_button.setEnabled(False)
        else:
            self.mode_button.setText('Auto mode: ON')
            self.mode_label.setText('Auto mode: OFF')
            self.message_input.setEnabled(True)
            self.state_input.setEnabled(True)
            self.send_button.setEnabled(True)

    def start_websocket(self):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp('ws://localhost:8081',
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def on_message(self, ws, message):
        try:
            if isinstance(message, bytes):
                message = message.decode('utf-8')

            data = json.loads(message)
            if isinstance(data, dict):
                if data.get('type') == 'client_message':
                    self.display_message(f"CLIENT: {data['text']}")
                elif data.get('type') == 'watson_response':
                    self.watson_response_received.emit(data)
                    if 'emotion' in data:
                        self.display_message(f"Emotion: {data['emotion']}")
                    if 'mood' in data:
                        self.display_message(f"Mood: {data['mood']}")
            else:
                self.display_message('SHARA: ' + str(message))
        except json.JSONDecodeError:
            self.display_message('SHARA: ' + message)
        except Exception as e:
            self.display_message('ERROR: ' + str(e))

    def handle_watson_response(self, data):
        if self.auto_mode:
            validated_response = data['text']
            validated_state = data.get('state', 'Attention')
            self.display_message(f"Watson: {validated_response}")
            self.display_message(f"Robot state: {validated_state}")
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps({
                    'type': 'wizard_message',
                    'text': validated_response,
                    'state': validated_state
                }))
        else:
            # Importing the WatsonResponseDialog class here to avoid circular imports
            from WatsonResponseDialog import WatsonResponseDialog
            current_state = data.get('state', 'Attention')
            dialog = WatsonResponseDialog(data['text'], current_state, self)
            if dialog.exec_() == QDialog.Accepted:
                validated_response = dialog.get_response()
                validated_state = dialog.get_state()
                self.display_message(f"Watson: {validated_response}")
                self.display_message(f"Robot state: {validated_state}")
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    self.ws.send(json.dumps({
                        'type': 'wizard_message',
                        'text': validated_response,
                        'state': validated_state
                    }))
                if 'emotion' in data:
                    self.display_message(f"Emotion: {data['emotion']}")
                if 'mood' in data:
                    self.display_message(f"Mood: {data['mood']}")
                    
    def on_error(self, ws, error):
        self.display_message('ERROR: ' + str(error))

    def on_close(self, ws):
        self.display_message('Close connection')

    def on_open(self, ws):
        self.display_message('Open connection')        

    def send_message(self):
        message = self.message_input.text()
        state = self.state_input.text() or 'Attention'
        if message.strip() != '':
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps({
                    'type': 'wizard_message',
                    'text': message,
                    'state': state
                }))
            self.display_message(f"Wizard: {message}")
            self.display_message(f"Robot state: {state}")
            self.message_input.clear()
            self.state_input.clear()

    def display_message(self, message):
        self.chat_display.append(message)

    def close_event(self, event):
        if self.ws:
            self.ws.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = ChatApplication()
    chat_app.setWindowTitle('Wizard of Oz Chat App')
    chat_app.setGeometry(100, 100, 500, 600)
    chat_app.show()
    sys.exit(app.exec_())