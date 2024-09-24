import sys
import numpy as np
import cv2
import asyncio
import qasync
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGridLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import pyqtSlot, QUrl
from ChatApplication import ChatApplication
from WebRTCClient import WebRTCClient, WebRTCThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wizard of Oz")
        self.label = QLabel(self)
        self.layout = QVBoxLayout()

        self.chat_app = ChatApplication()

        #self.web_view = QWebEngineView()
        #self.web_view.load(QUrl("http://localhost:5173"))

        self.webrtc_client = WebRTCClient()
        self.webrtc_client.frame_received.connect(self.on_frame_recived)
        self.webrtc_thread = WebRTCThread(self.webrtc_client)
        self.webrtc_thread.start()

        self.layout = QGridLayout()

        self.layout.addWidget(self.label, 0, 0)
        #self.layout.addWidget(self.web_view, 0, 1)
        self.layout.addWidget(self.chat_app, 1, 0, 1, 2)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        

    @pyqtSlot(np.ndarray)
    def on_frame_recived(self, frame_data):
        rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)

        height, width, channel = rgb_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_data.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_image))

async def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        await loop.run_forever()

if __name__ == "__main__":
    asyncio.run(main())