import sys
import threading
import json
import asyncio
import qasync
from qasync import QEventLoop, asyncSlot
import socketio
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QDialog, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QObject, QTimer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SockeIOtHandle(QObject):
    message_received = pyqtSignal(str)
    connection_opened = pyqtSignal()
    connection_closed = pyqtSignal(str)
    connection_error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        self.setup_events()

    def setup_events(self):
        @self.sio.event
        async def connect():
            logger.info('Connected to server')
            self.connection_opened.emit()

        @self.sio.event
        async def disconnect():
            logger.info('Disconnected from server')
            self.connection_closed.emit('Disconnected')

        @self.sio.event
        async def message(data):
            logger.info(f'Message received: {data}')
            self.message_received.emit(json.dumps(data))

        @self.sio.on('*')
        def catch_all_event(event, data):
            logger.info(f'Catch all event: {event} - {data}')
            self.message_received.emit(json.dumps({'event': event, 'data': data}))

    async def connect(self):
        try:
            await self.sio.connect(self.url)
        except Exception as e:
            logger.error(f'Error connecting to server: {str(e)}')
            self.connection_error.emit(str(e))

    async def disconnect(self):
        await self.sio.disconnect()

    async def send_message(self, message):
        try:
            await self.sio.emit('message', message)
        except Exception as e:
            logger.error(f'Error sending message: {str(e)}')
            self.connection_error.emit(str(e))

class ChatApplication(QWidget):
    watson_response_received = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ChatApplication, self).__init__(parent)
        self.socket_client = SockeIOtHandle('http://localhost:8081')
        self.socket_client.message_received.connect(self.handle_message)
        self.socket_client.connection_opened.connect(self.handle_connection_opened)
        self.socket_client.connection_closed.connect(self.handle_connection_closed)
        self.socket_client.connection_error.connect(self.handle_connection_error)
        self.socket_client.connect()
        self.create_widgets()
        self.watson_response_received.connect(self.handle_watson_response)
        self.auto_mode = False

        asyncio.get_event_loop().create_task(self.connect_scoket())

    async def connect_scoket(self):
        await self.socket_client.connect()

    def handle_message(self, message):
        try:
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
                self.display_message(f'SHARA: {message}')
        except json.JSONDecodeError:
            self.display_message(f'SHARA: {message}')
        except Exception as e:
            logger.error(f'ERROR processing message: {str(e)}')
            self.display_message(f'ERROR processing message: {str(e)}')

    def handle_connection_opened(self):
        self.display_message('WebSocket connection established')

    def handle_connection_closed(self, close_info):
        self.display_message(f'WebSocket connection closed: {close_info}')

    def handle_connection_error(self, error):
        self.display_message(f'WebSocket connection error: {error}')

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
        self.send_button.clicked.connect(self.on_send_clicked)
        button_layout.addWidget(self.send_button)

        self.mode_button = QPushButton('Auto mode')
        self.mode_button.clicked.connect(self.toggle_mode)
        button_layout.addWidget(self.mode_button)

        self.layout.addLayout(button_layout)

        self.mode_label = QLabel('Auto mode: OFF')
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

    async def handle_watson_response(self, data):
        if self.auto_mode:
            validated_response = data['text']
            validated_state = data.get('state', 'Attention')
            self.display_message(f"Watson: {validated_response}")
            self.display_message(f"Robot state: {validated_state}")
            await self.socket_client.send(json.dumps({
                'type': 'wizard_message',
                'text': validated_response,
                'state': validated_state
            }))
        else:
            # Importing the WatsonResponseDialog class here to avoid circular imports
            from WatsonResponseDialog import WatsonResponseDialog
            current_state = data.get('state', 'Attention')
            dialog = WatsonResponseDialog(data['text'], current_state, self)
            if dialog.exec() == QDialog.accepted:
                validated_response = dialog.get_response()
                validated_state = dialog.get_state()
                self.display_message(f"Watson: {validated_response}")
                self.display_message(f"Robot state: {validated_state}")
                await self.socket_client.send(json.dumps({
                    'type': 'wizard_message',
                    'text': validated_response,
                    'state': validated_state
                }))
                if 'emotion' in data:
                    self.display_message(f"Emotion: {data['emotion']}")
                if 'mood' in data:
                    self.display_message(f"Mood: {data['mood']}")
                    
    def on_error(self, ws, error):
        self.display_message(f'WebSocket error: {str(error)}')

    def on_close(self, ws, close_status_code, close_msg):
        self.display_message(f'Close connection: {close_status_code} - {close_msg}')
        threading.Timer(5, self.start_websocket).start()

    def on_open(self, ws):
        self.display_message('Open connection')        

    @asyncSlot()
    async def on_send_clicked(self):
        await self.send_message()

    async def send_message(self):
        message = self.message_input.text()
        state = self.state_input.text() or 'Attention'
        if message.strip() != '':
            self.socket_client.send_message(json.dumps({
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
        asyncio.get_event_loop().create_task(self.close_application())
        event.accept()

    async def close_application(self): 
        await self.socket_client.disconnect()

async def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    chat_app = ChatApplication()
    chat_app.setWindowTitle('Wizard of Oz Chat App')
    chat_app.setGeometry(100, 100, 500, 600)
    chat_app.show()

    with loop:
        await loop.run_forever()

if __name__ == '__main__':
    qasync.run(main())