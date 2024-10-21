import asyncio
import cv2
import numpy as np
import websockets
import json
import base64
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, Qt

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketThread(QThread):
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
            self.websocket = await websockets.connect('ws://localhost:8081/socket', ping_interval=20, ping_timeout=20)
            logging.info("Connected to server")
            self.connection_status.emit("Connected to server")
            await self.websocket.send(json.dumps({"type": "register", "client": "python"}))
            logging.info("Registered as python client")
        except Exception as e:
            logging.error(f"Connection failed: {str(e)}")
            self.connection_status.emit(f"Connection failed: {str(e)}")
            self.websocket = None

    async def run_async(self):
        while self.running:
            try:
                if not self.websocket:
                    await self.connect()
                    if not self.websocket:
                        await asyncio.sleep(5)
                        continue

                logging.debug("Waiting for message")
                message = await self.websocket.recv()
                logging.debug(f"Received message: {message[:100]}...")

                data = json.loads(message)
                if data['type'] == 'video':
                    frame_data = base64.b64decode(data['frame'].split(',')[1])
                    frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                    self.frame_received.emit(frame)
                    self.frames_received += 1
                    if self.frames_received % 100 == 0:
                        logging.info(f"Received {self.frames_received} frames")
                else:
                    logging.warning(f"Received unknown message type: {data['type']}")

            except websockets.exceptions.ConnectionClosed:
                logging.warning("Connection closed. Reconnecting...")
                self.connection_status.emit("Connection closed. Reconnecting...")
                self.websocket = None
            except json.JSONDecodeError:
                logging.error(f"Failed to decode JSON: {message}")
            except Exception as e:
                logging.error(f"Error in WebSocket thread: {str(e)}")
                self.connection_status.emit(f"Error: {str(e)}")
                self.websocket = None

            if not self.websocket:
                await asyncio.sleep(5)

    def run(self):
        asyncio.run(self.run_async())

    def stop(self):
        self.running = False
        if self.websocket:
            asyncio.run(self.websocket.close())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 WebSocket Video Test")
        self.setGeometry(100, 100, 640, 480)
        
        layout = QVBoxLayout()
        
        self.video_label = QLabel()
        layout.addWidget(self.video_label)
        
        self.status_label = QLabel("Status: Initializing...")
        layout.addWidget(self.status_label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.websocket_thread = WebSocketThread()
        self.websocket_thread.connection_status.connect(self.update_status)
        self.websocket_thread.frame_received.connect(self.display_frame)
        self.websocket_thread.start()

    def display_frame(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        logging.debug("Frame displayed")

    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")
        logging.info(f"Status updated: {status}")

    def closeEvent(self, event):
        self.websocket_thread.stop()
        self.websocket_thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    logging.info("Starting application")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()