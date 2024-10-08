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
    video_chunk_received = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        self.setup_events()
        self.video_subscribed = False

    def setup_events(self):
        @self.sio.event
        async def connect():
            logger.info('SocketIO connection established')
            self.connection_opened.emit()

        @self.sio.event
        async def disconnect():
            logger.info('Disconnected from server')
            self.connection_closed.emit('Disconnected')

        @self.sio.on('*')
        async def catch_all(event, data):
            if event == 'video_chunk':
                if self.video_subscribed:
                    self.video_chunk_received.emit(data)
                return 
            logger.info(f'Received event: {event}, data: {data}')
            
            self.message_received.emit(json.dumps({'event': event, 'data': data}))

        @self.sio.event
        async def message(data):
            logger.info(f'Message received: {data}')
            self.message_received.emit(json.dumps(data))

    async def connect(self):
        try:
            logger.info(f'Attempting to connect to server: {self.url}')
            await self.sio.connect(self.url, transports=['websocket'])
            logger.info(f'Connected to server: {self.url}')

            await self.sio.emit('register_python_client')
            logger.info('Registered Python client')
        except Exception as e:
            logger.error(f'Error connecting to server: {str(e)}')
            self.connection_error.emit(str(e))

    async def disconnect(self):
        if self.sio.connected:
            await self.sio.disconnect()
        logger.info('Disconnected from server')

    async def subscribe_video(self):
        await self.sio.emit('subscribe_video')
        self.video_subscribed = True
        logger.info('Subscribed to video chunks')

    async def unsubscribe_video(self):
        await self.sio.emit('unsubscribe_video')
        self.video_subscribed = False
        logger.info('Unsubscribed from video chunks')

    async def send_message(self, message):
        if not self.sio.connected:
            logger.error('SocketIO connection not established')
            return
        try:
            await self.sio.emit('message', message)
            logger.info(f'Message sent: {message}')
        except Exception as e:
            logger.error(f'Error sending message: {str(e)}')
            self.connection_error.emit(str(e))