import threading
import asyncio
import json
import os
from pathlib import Path
from qasync import asyncSlot
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QLabel, QComboBox, QFrame, QScrollArea, QButtonGroup
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
from SockeIOtHandle import SockeIOtHandle
from WatsonResponseDialog import WatsonResponseDialog
from config import VITE_SERVER_URL

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

ROOT_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = os.path.join(ROOT_DIR, 'icons')

class StyledChatDisplay(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                padding: 10px;
                border-radius: 5px;
                font-size: 13px;
            }
        """)

    def append(self, text):
        if text.startswith('CLIENT:'):
            color = '#2980b9'
        elif text.startswith('Watson:'):
            color = '#27ae60'
        elif text.startswith('Wizard:'):
            color = '#8e44ad'
        elif text.startswith('Robot state:'):
            color = '#e67e22'
        else:
            color = '#7f8c8d'

        formatted_text = f'<div style="color: {color}; margin: 5px 0;">{text}</div>'
        super().append(formatted_text)

class StyledButton(QPushButton):
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        if icon_name:
            icon_path = os.path.join(ICONS_DIR, f"{icon_name}.png")
            if os.path.exists(icon_path):
                self.setIcon(QIcon(icon_path))
            else:
                logger.warning(f"Icon not found: {icon_path}")

class StateButton(QPushButton):
    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.state = state
        self.setCheckable(True)
        self.setFixedSize(100, 70)

        icon_path = os.path.join(ICONS_DIR, f"{state.lower()}.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(30, 30))
        else:
            logger.warning(f"Icon not found: {icon_path}")
            self.setText(state[:1])

        self.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                margin: 2px;
            }
            QPushButton:checked {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #2c3e50;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:checked:hover {
                background-color: #34495e;
            }
        """)

        self.setToolTip(state)

class StateButtonGroup(QWidget):
    stateChanged = pyqtSignal(str)

    def __init__(self, states, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Crear botones para cada estado
        for state in states:
            button = StateButton(state)
            self.layout.addWidget(button)
            self.button_group.addButton(button)
            
        # Conectar la señal del grupo de botones
        self.button_group.buttonClicked.connect(self._on_button_clicked)
        
        # Seleccionar el primer estado por defecto
        if states:
            self.button_group.buttons()[0].setChecked(True)
    
    def _on_button_clicked(self, button):
        self.stateChanged.emit(button.state)
        
    def get_current_state(self):
        checked_button = self.button_group.checkedButton()
        return checked_button.state if checked_button else None


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
        self.auto_mode = False
        self.connection_retries = 0
        self.max_retries = 5
        self.active_dialog = None

        self.setup_ui_components()
        self.setup_socket_client()
        self.setup_timers()
        self.dialog_response.connect(self.handle_dialog_response)
        

    def setup_ui_components(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        #Status bar
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 5px;")
        status_layout = QHBoxLayout(status_frame)
        
        self.connection_label = QLabel("Desconectado")
        self.connection_label.setStyleSheet("color: #e74c3c;")
        status_layout.addWidget(self.connection_label)
        
        self.mode_label = QLabel("Modo Manual")
        self.mode_label.setStyleSheet("color: #2980b9;")
        status_layout.addWidget(self.mode_label)
        
        main_layout.addWidget(status_frame)

        # Chat display
        self.chat_display = StyledChatDisplay()
        main_layout.addWidget(self.chat_display)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 5px;")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(5)

        # Message input
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Escribe tu mensaje aquí...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        message_layout.addWidget(self.message_input)

        self.send_button = StyledButton("Enviar", "send")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_button.setEnabled(True)
        message_layout.addWidget(self.send_button)

        input_layout.addLayout(message_layout)

        self.state_buttons = StateButtonGroup(WatsonResponseDialog.get_all_states())
        input_layout.addWidget(self.state_buttons)

        button_layout = QHBoxLayout()
        self.mode_button = StyledButton("Modo Auto", "auto")
        self.mode_button.clicked.connect(self.toggle_mode)
        button_layout.addWidget(self.mode_button)
        input_layout.addLayout(button_layout)

        main_layout.addWidget(input_frame)

    def setup_socket_client(self):
        self.socket_client = SockeIOtHandle(VITE_SERVER_URL)
        self.socket_client.message_received.connect(self.handle_message)
        self.socket_client.connection_opened.connect(self.handle_connection_opened)
        self.socket_client.connection_closed.connect(self.handle_connection_closed)
        self.socket_client.connection_error.connect(self.handle_connection_error)
        self.socket_client.registration_confirmed.connect(self.handle_registration_confirmed)

    def setup_timers(self):
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
            self.chat_display.append(f'Error initializing WebSocket connection: {str(e)}')

    async def cleanup(self):
        logger.info('Cleaning up WebSocket connection')
        try:
            await self.socket_client.disconnect()
            logger.info('WebSocket connection cleaned up')
        except Exception as e:
            logger.error(f'Error cleaning up WebSocket connection: {str(e)}')
            self.chat_display.append(f'Error cleaning up WebSocket connection: {str(e)}')

    def update_connection_status(self, status, connected=False):
        self.connection_label.setText(status)
        self.connection_label.setStyleSheet(
            f"color: {'#27ae60' if connected else '#e74c3c'}; font-weight: bold;"
        )

    def handle_message(self, message):
        try:
            data = json.loads(message)
            logger.info(f'Message received: {data}')
            if isinstance(data, dict):
                event = data.get('event')
                event_data = data.get('data')
                if event == 'client_message':
                    self.chat_display.append(f"CLIENT: {event_data['text']}")
                elif event == 'watson_message':
                    self.handle_watson_response(event_data)
                else:
                    self.chat_display.append(f'EVENT: {event}, DATA: {event_data}')
            else:
                self.chat_display.append(f'SHARA: {message}')
        except json.JSONDecodeError:
            self.chat_display.append(f'SHARA Non JSON: {message}')
        except Exception as e:
            logger.error(f'ERROR processing message: {str(e)}')
            self.chat_display.append(f'ERROR processing message: {str(e)}')

    def handle_registration_confirmed(self):
        self.update_connection_status('Registered', True)
        self.send_button.setEnabled(True)

    def handle_connection_opened(self):
        logger.info('WebSocket connection established')
        self.update_connection_status('Conectado', True)
        self.chat_display.append('WebSocket connection established')

    def handle_connection_closed(self, close_info):
        logger.info(f'WebSocket connection closed: {close_info}')
        self.update_connection_status('Desconectado')
        self.chat_display.append(f'WebSocket connection closed: {close_info}')

    def handle_connection_error(self, error):
        logger.error(f'WebSocket connection error: {error}')
        self.update_connection_status('Error')
        self.chat_display.append(f'WebSocket connection error: {error}')

    def quit(self):
        self.event_service_process.terminate()
        super().quit()

    def toggle_mode(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.mode_button.setText('Modo Manual')
            self.mode_label.setText('Modo Automático')
            self.mode_label.setStyleSheet("color: #27ae60;")
            self.message_input.setEnabled(False)
            self.state_buttons.setEnabled(False)
            self.send_button.setEnabled(False)
        else:
            self.mode_button.setText('Modo Auto')
            self.mode_label.setText('Modo Manual')
            self.mode_label.setStyleSheet("color: #2980b9;")
            self.message_input.setEnabled(True)
            self.state_buttons.setEnabled(True)
            self.send_button.setEnabled(True)

    @asyncSlot()
    async def handle_watson_response(self, data):
        logger.info('Handling Watson response')
        if self.auto_mode:
            validated_response = data['text']
            validated_state = data.get('state', 'Attention')
            self.chat_display.append(f"Watson: {validated_response}")
            self.chat_display.append(f"Robot state: {validated_state}")
            await self.socket_client.send_message({
                'type': 'wizard_message',
                'text': validated_response,
                'state': validated_state
            })
        else:
            if self.active_dialog is not None:
                self.active_dialog.close()

            if data['text'] == '':
                await self.socket_client.send_message({
                    'type': 'wizard_message',
                    'text': '',
                    'state': 'Sad'
                })
            else:
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
        self.chat_display.append(f"Watson: {response}")
        self.chat_display.append(f"Robot state: {state}")
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
            self.chat_display.append(f"Error sending message: {e}")
                
    def on_error(self, ws, error):
        self.chat_display.append(f'WebSocket error: {str(error)}')

    def on_close(self, ws, close_status_code, close_msg):
        self.chat_display.append(f'Close connection: {close_status_code} - {close_msg}')
        threading.Timer(5, self.start_websocket).start()

    def on_open(self, ws):
        self.chat_display.append('Open connection')        

    @asyncSlot()
    async def on_send_clicked(self):
        await self.send_message()

    async def send_message(self):
        if not self.message_input.text().strip():
            return

        message = self.message_input.text()
        state = self.state_buttons.get_current_state()
        
        try:
            await self.socket_client.send_message({
                'type': 'wizard_message',
                'text': message,
                'state': state
            })
            self.chat_display.append(f"Wizard: {message}")
            self.chat_display.append(f"Robot state: {state}")
            self.message_input.clear()
        except Exception as e:
            self.chat_display.append(f"Error al enviar mensaje: {str(e)}")

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

