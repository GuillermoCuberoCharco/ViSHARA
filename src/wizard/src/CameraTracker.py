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
        
        self.websocket_client = WebSocketClient()
        self.websocket_client.frame_received.connect(self.display_frame)
   
        asyncio.get_event_loop().create_task(self.websocket_client.connect())

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

    async def connect(self):
        try:
            logging.debug("Attempting to connect to WebSocket server...")
            self.websocket = await websockets.connect(f'{VITE_SERVER_URL.replace("https", "wss")}/video-socket', ping_interval=20, ping_timeout=20)
            logging.info("Connected to server")
            self.connection_status.emit("Connected to server")
            await self.websocket.send(json.dumps({"type": "register", "client": "python"}))
            logging.info("Registered as python client")
            await self.receive_messages()
        except Exception as e:
            logging.error(f"Connection failed: {str(e)}")
            self.connection_status.emit(f"Connection failed: {str(e)}")
            self.websocket = None
            await asyncio.sleep(5)
            if self.running:
                asyncio.create_task(self.connect())

    async def receive_messages(self):
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'video':
                    frame_data = base64.b64decode(data['frame'].split(',')[1])
                    frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                    self.frame_received.emit(frame)
                    self.frames_received += 1
                    if self.frames_received % 100 == 0:
                        logging.info(f"Received {self.frames_received} frames")
                
            except websockets.exceptions.ConnectionClosed:
                logging.warning("Connection closed. Reconnecting...")
                self.connection_status.emit("Connection closed. Reconnecting...")
                self.websocket = None
                break
            except Exception as e:
                logging.error(f"Error in receive_messages: {str(e)}")
                break

        if self.running:
            await asyncio.sleep(5)
            asyncio.create_task(self.connect())

    async def stop(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None