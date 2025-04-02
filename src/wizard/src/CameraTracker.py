import asyncio
import cv2
import numpy as np
import websockets
import json
import base64
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QObject
from config import VITE_SERVER_URL

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CameraTracker")

class VideoFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 8px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: none;")
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.video_label)
    
class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        self.video_frame = VideoFrame()
        layout.addWidget(self.video_frame, stretch=1)

        self.status_label = QLabel("Connecting to server...")
        self.status_label.setStyleSheet("color: #e74c3c; background-color: rgba(0,0,0,0.5); padding: 2px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.websocket_client = WebSocketClient()
        self.websocket_client.frame_received.connect(self.display_frame)
        self.websocket_client.connection_status.connect(self.update_status)
   
        asyncio.get_event_loop().create_task(self.websocket_client.connect())

    @pyqtSlot(str)
    def update_status(self, status):
        self.status_label.setText(status)
        if "Connected" in status:
            self.status_label.setStyleSheet("color: #2ecc71; background-color: rgba(0,0,0,0.5); padding: 2px;")
        else:
            self.status_label.setStyleSheet("color: #e74c3c; background-color: rgba(0,0,0,0.5); padding: 2px;")

    @pyqtSlot(np.ndarray)
    def display_frame(self, frame):
        try:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            
            label_size = self.video_frame.video_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_frame.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logging.error(f"Error displaying frame: {str(e)}")

    async def cleanup(self):
        if hasattr(self, 'websocket_client'):
            await self.websocket_client.stop()

class WebSocketClient(QObject):
    connection_status = pyqtSignal(str)
    frame_received = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.running = True
        self.websocket = None
        self.frames_received = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5

    async def connect(self):
        try:
            ws_url = f'{VITE_SERVER_URL.replace("https://", "wss://").replace("http://", "ws://")}'
            logging.debug("Attempting to connect to WebSocket server at ´{ws_url}/video-socket´")
            self.websocket = await websockets.connect(f'{ws_url}/video-socket', ping_interval=20, ping_timeout=20, close_timeout=5)
            logging.info("Connected to server")
            self.connection_status.emit("Connected to server")
            self.reconnect_attempts = 0
            await self.websocket.send(json.dumps({"type": "register", "client": "python"}))
            logging.info("Registered as python client")
            await self.receive_messages()
        except Exception as e:
            logging.error(f"Connection failed: {str(e)}")
            self.connection_status.emit(f"Connection failed: {str(e)}")
            self.websocket = None
            self.reconnect_attempts += 1
            if self.reconnect_attempts <= self.max_reconnect_attempts:
                delay = min(30, self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)))
                self.connection_status.emit(f"Reconnecting in {delay} seconds...")
                await asyncio.sleep(delay)
                if self.running:
                    asyncio.create_task(self.connect())
            else:
                self.connection_status.emit("Max reconnect attempts reached. Stopping.")

    async def receive_messages(self):
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)

                logging.debug(f"Received message type: {data.get('type')}")

                if data.get('type') == 'registration_success':
                    logging.info("Registration successful")
                    self.connection_status.emit("Registration confirmed")
                elif data.get('type') == 'video-frame' or 'frame' in data:
                    frame_data = data.get('frame', '')
                    
                    if frame_data and ',' in frame_data:
                        frame_data = base64.b64decode(frame_data.split(',')[1])
                        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            self.frame_received.emit(frame)
                            self.frames_received += 1
                            if self.frames_received % 100 == 0:
                                logging.info(f"Received {self.frames_received} frames")
                        else:
                            logging.warning("Received empty frame")
                    else:
                        logging.warning(f"Invalid frame data format: {frame_data[:30]}...")

            except websockets.exceptions.ConnectionClosed as e:
                logging.warning(f"Connection closed: {str(e)}. Reconnecting...")
                self.connection_status.emit(f"Connection closed: {str(e)}. Reconnecting...")
                self.websocket = None
                break
            except Exception as e:
                logging.error(f"Error in receive_messages: {str(e)}")
                self.connection_status.emit(f"Error in receive_messages: {str(e)}")
                break

        if self.running:
            await asyncio.sleep(self.reconnect_delay)
            asyncio.create_task(self.connect())

    async def stop(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None