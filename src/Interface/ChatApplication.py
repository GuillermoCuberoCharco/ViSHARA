import threading
import asyncio
import json
from qasync import asyncSlot
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QDialog, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from SockeIOtHandle import SockeIOtHandle
from WatsonResponseDialog import WatsonResponseDialog

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

class NonBlockingWatsonDialog(WatsonResponseDialog):
    finished = pyqtSignal(bool, str, str)

    def __init__(self, response, current_state, parent=None):
        super().__init__(response, current_state, parent)
        self.setWindowModality(Qt.WindowModality.NonModal)

    def accept(self):
        response = self.get_response()
        state = self.get_state()
        self.finished.emit(True, response, state)
        super().accept()

    def reject(self):
        self.finished.emit(False, '', '')
        super().reject()

class ChatApplication(QWidget):
    dialog_response = pyqtSignal(bool, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info('Initializing ChatApplication')
        self.socket_client = SockeIOtHandle('http://localhost:8081')
        self.socket_client.message_received.connect(self.handle_message)
        self.socket_client.connection_opened.connect(self.handle_connection_opened)
        self.socket_client.connection_closed.connect(self.handle_connection_closed)
        self.socket_client.connection_error.connect(self.handle_connection_error)
        self.socket_client.registration_confirmed.connect(self.handle_registration_confirmed)
        self.create_widgets()
        self.auto_mode = False
        self.connection_retries = 0
        self.max_retries = 5

        self.active_dialog = None

        self.dialog_response.connect(self.handle_dialog_response)

        self.keepalive_timer = QTimer(self)
        self.keepalive_timer.timeout.connect(self.send_keepalive)
        self.keepalive_timer.start(30000)

    @asyncSlot()
    async def send_keepalive(self):
        if self.socket_client and not self.active_dialog:
            try:
                await self.socket_client.sio.emit('ping')
            except Exception as e:
                print(f"Error sending keepalive: {e}")


    async def initialize(self):
        try:
            retries = 0
            max_retries = 5
            while retries < max_retries:
                try:
                    self.socket_client.sio.transports = ['polling']
                    await self.socket_client.connect()
                    logger.info('Connected successfully')
                    break
                except Exception as e:
                    retries += 1
                    logger.error(f'Connection attempt {retries} failed: {str(e)}')
                    if retries < max_retries:
                        await asyncio.sleep(5)
                    else:
                        raise Exception("Max connection retries reached")
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

    def update_connection_status(self, status):
        self.mode_label.setText(f'Connection: {status}')

    def handle_registration_confirmed(self):
        self.update_connection_status('Registered')
        self.send_button.setEnabled(True)

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
            if self.active_dialog is not None:
                self.active_dialog.close()

            current_state = data.get('state', 'Attention')
            dialog = NonBlockingWatsonDialog(data['text'], current_state, self)
            dialog.finished.connect(self.handle_dialog_response)
            self.active_dialog = dialog
            dialog.show()

    def handle_dialog_response(self, accepted, response, state):
        self.active_dialog = None
        if accepted:
            QTimer.singleShot(0, lambda: self.schedule_message_send(response, state))
    
    def schedule_message_send(self, response, state):
        self.display_message(f"Watson: {response}")
        self.display_message(f"Robot state: {state}")
        loop = asyncio.get_event_loop()
        loop.create_task(self.send_message_async(response, state))

    async def send_message_async(self, response, state):
        try:
            await self.socket_client.send_message({
                'type': 'wizard_message',
                'text': response,
                'state': state
            })
        except Exception as e:
            print(f"Error sending message: {e}")
            self.display_message(f"Error sending message: {e}")
                
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

    def closeEvent(self, event):
        if self.active_dialog:
            self.active_dialog.close()
        self.keepalive_timer.stop()
        event.accept()

    @asyncSlot()
    async def close_application(self): 
        logger.info('Closing ChatApplication')
        await self.cleanup()
        QApplication.instance().quit()

