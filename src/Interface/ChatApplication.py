import sys
import threading
import json
import asyncio
import qasync
from qasync import QEventLoop, asyncSlot, QApplication
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QDialog, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from SockeIOtHandle import SockeIOtHandle
from WatsonResponseDialog import WatsonResponseDialog

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

class ChatApplication(QWidget):
    watson_response_received = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ChatApplication, self).__init__(parent)
        logger.info('Initializing ChatApplication')
        self.socket_client = SockeIOtHandle('http://localhost:8081')
        self.socket_client.message_received.connect(self.handle_message)
        self.socket_client.connection_opened.connect(self.handle_connection_opened)
        self.socket_client.connection_closed.connect(self.handle_connection_closed)
        self.socket_client.connection_error.connect(self.handle_connection_error)
        self.create_widgets()
        self.auto_mode = False

    async def initialize(self):
        try:
            await self.socket_client.connect()
            logger.info('WebSocket connection initialized')
        except Exception as e:
            logger.error(f'Error initializing WebSocket connection: {str(e)}')
            self.display_message(f'Error initializing WebSocket connection: {str(e)}')

    async def cleanup(self):
        logger.info('Cleaning up WebSocket connection')
        try:
            await self.socket_client.disconnect()
            logger.info('WebSocket connection cleaned up')
        except Exception as e:
            logger.error(f'Error cleaning up WebSocket connection: {str(e)}')
            self.display_message(f'Error cleaning up WebSocket connection: {str(e)}')

    def handle_message(self, message):
        try:
            data = json.loads(message)
            logger.info(f'Message received: {data}')
            if isinstance(data, dict):
                event = data.get('event')
                event_data = data.get('data')
                if event == 'client_message':
                    self.display_message(f"CLIENT: {event_data['text']}")
                elif event == 'watson_message':
                    self.handle_watson_response(event_data)
                else:
                    self.display_message(f'EVENT: {event}, DATA: {event_data}')
            else:
                self.display_message(f'SHARA: {message}')
        except json.JSONDecodeError:
            self.display_message(f'SHARA Non JSON: {message}')
        except Exception as e:
            logger.error(f'ERROR processing message: {str(e)}')
            self.display_message(f'ERROR processing message: {str(e)}')

    def handle_connection_opened(self):
        logger.info('WebSocket connection established')
        self.display_message('WebSocket connection established')

    def handle_connection_closed(self, close_info):
        logger.info(f'WebSocket connection closed: {close_info}')
        self.display_message(f'WebSocket connection closed: {close_info}')

    def handle_connection_error(self, error):
        logger.error(f'WebSocket connection error: {error}')
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

    @asyncSlot()
    async def handle_watson_response(self, data):
        logger.info('Handling Watson response')
        if self.auto_mode:
            validated_response = data['text']
            validated_state = data.get('state', 'Attention')
            self.display_message(f"Watson: {validated_response}")
            self.display_message(f"Robot state: {validated_state}")
            await self.socket_client.send_message({
                'type': 'wizard_message',
                'text': validated_response,
                'state': validated_state
            })
        else:
            current_state = data.get('state', 'Attention')
            dialog = WatsonResponseDialog(data['text'], current_state, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                validated_response = dialog.get_response()
                validated_state = dialog.get_state()
                self.display_message(f"Watson: {validated_response}")
                self.display_message(f"Robot state: {validated_state}")
                await self.socket_client.send_message({
                    'type': 'wizard_message',
                    'text': validated_response,
                    'state': validated_state
                })
                
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
            await self.socket_client.send_message(({
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
        logger.info('Close event received')
        asyncio.create_task(self.cleanup())
        event.accept()

    async def close_application(self): 
        logger.info('Closing ChatApplication')
        await self.socket_client.disconnect()

async def main():
    logger.info('Starting ChatApplication')
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    logger.info('Creating ChatApplication')
    chat_app = ChatApplication()
    chat_app.setWindowTitle('Wizard of Oz Chat App')
    chat_app.setGeometry(100, 100, 500, 600)
    chat_app.show()

    logger.info('Running ChatApplication')
    await chat_app.initialize()

    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    future = asyncio.Future()

    app.lastWindowClosed.connect(lambda: close_future(future, loop))

    try:
        await future
    except asyncio.CancelledError:
        pass
    finally:
        await chat_app.close_application()

if __name__ == '__main__':
    qasync.run(main())