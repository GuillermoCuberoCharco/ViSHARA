import json
import socketio
import logging
from PyQt6.QtCore import pyqtSignal, QObject

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SockeIOtHandle(QObject):
    message_received = pyqtSignal(str)
    connection_opened = pyqtSignal()
    connection_closed = pyqtSignal(str)
    connection_error = pyqtSignal(str)
    registration_confirmed = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url
        engineio_opts = {
            'logger': True,
            'engineio_logger': True
        }
        self.sio = socketio.AsyncClient(engineio_opts)
        self.setup_events()
        self.is_registered = False

    def setup_events(self):
        @self.sio.event
        async def connect():
            logger.info('SocketIO connection established')
            self.connection_opened.emit()
            if not self.is_registered:
                try:
                    await self.sio.emit('register_operator', 'python')
                    logger.info('Python client registered')
                except Exception as e:
                    logger.error(f'Error registering Python client: {str(e)}')

        @self.sio.event
        async def registration_confirmed():
            logger.info('Registration confirmed')
            self.is_registered = True
            self.registration_confirmed.emit()
            
        @self.sio.event
        async def connect_error(error):
            logger.error(f'Connection error: {error}')
            self.connection_error.emit(str(error))

        @self.sio.event
        async def disconnect():
            logger.info('Disconnected from server')
            self.connection_closed.emit('Disconnected')

        @self.sio.event
        async def client_message(data):
            logger.info(f'Client message received: {data}')
            self.message_received.emit(json.dumps({
                'event': 'client_message',
                'data': data
            }))

        @self.sio.event
        async def watson_message(data):
            logger.info(f'Watson message received: {data}')
            self.message_received.emit(json.dumps({
                'event': 'watson_message',
                'data': data
            }))

        @self.sio.event
        async def wizard_message(data):
            logger.info(f'Wizard message received: {data}')
            self.message_received.emit(json.dumps({
                'event': 'wizard_message',
                'data': data
            }))

    async def connect(self):
        try:
            logger.info(f'Attempting to connect to server: {self.url}')
            await self.sio.connect(
                self.url,
                transports=['websocket', 'polling'],
                wait=True,
                wait_timeout=10
            )
            logger.info('Connected to server')
            self.connection_opened.emit()
        except Exception as e:
            logger.error(f'Error connecting to server: {str(e)}')
            self.connection_error.emit(str(e))
            raise

    async def disconnect(self):
        if self.sio.connected:
            await self.sio.disconnect()
            logger.info('Disconnected from server')

    async def send_message(self, message):
        if not self.sio.connected:
            logger.error('SocketIO connection not established')
            self.connection_error.emit('SocketIO connection not established')
            return False
        try:
            await self.sio.emit('message', message)
            logger.info(f'Message sent: {message}')
            return True
        except Exception as e:
            logger.error(f'Error sending message: {str(e)}')
            self.connection_error.emit(str(e))
            return False