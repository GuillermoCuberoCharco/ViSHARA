import sys
import threading
import json
import websocket
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QDialog
from PyQt5.QtCore import pyqtSignal

class ChatApplication(QWidget):
    watson_response_received = pyqtSignal(dict)
    def __init__(self, parent=None):
        super(ChatApplication, self).__init__(parent)
        self.create_widgets()
        self.ws = None
        self.watson_response_received.connect(self.handle_watson_response)
        threading.Thread(target=self.start_websocket, daemon=True).start()

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
        self.message_input.returnPressed.connect(self.send_message)
        self.layout.addWidget(self.message_input)

        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_button)

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
        from WatsonResponseDialog import WatsonResponseDialog
        dialog = WatsonResponseDialog(data['text'], self)
        if dialog.exec_() == QDialog.Accepted:
            validated_response = dialog.get_response()
            self.display_message(f"Watson: {validated_response}")
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps({
                    'type': 'wizard_message',
                    'text': validated_response,
                    'state' : 'Attention'
                }))
            if 'emotion' in data:
                self.display_message(f"Emotion: {data['emotion']}")
            if 'mood' in data:
                self.display_message(f"Mood: {data['mood']}")

    def on_error(self, ws, error):
        self.display_message('ERROR: ' + str(error))

    def on_close(self, ws):
        self.display_message('CONNECTION CLOSED')

    def on_open(self, ws):
        self.display_message('CONNECTION OPENED')        

    def send_message(self):
        message = self.message_input.text()
        if message.strip() != '':
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps({
                    'type': 'wizard_message',
                    'text': message,
                    'state' : 'Attention'
                }))
            self.display_message(f"Wizzard: {message}")
            self.message_input.clear()

    def display_message(self, message):
        self.chat_display.append(message)

    def close_event(self, event):
        if self.ws:
            self.ws.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = ChatApplication()
    chat_app.setWindowTitle('Wizard Chat Application')
    chat_app.setGeometry(100, 100, 400, 500)
    chat_app.show()
    sys.exit(app.exec_())