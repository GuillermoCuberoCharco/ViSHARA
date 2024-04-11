from PyQt5.QtWebSockets import QWebSocket, QWebSocketProtocol
from PyQt5.QtCore import QUrl, QJsonDocument
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ChatApplication import ChatApplication
import cv2
import numpy as np
import tempfile
import os
import threading


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Mi Aplicación")

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        web_view = QWebEngineView()
        web_view.load(QUrl("http://localhost:5173/"))
        layout.addWidget(web_view)

        self.camera_view = QLabel()
        layout.addWidget(self.camera_view)

        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_textMessageReceived)
        self.websocket.binaryMessageReceived.connect(
            self.on_binaryMessageReceived)
        self.websocket.error.connect(self.on_error)

        self.websocket.open(QUrl("ws://localhost:8084"))

        self.chat_app = ChatApplication()
        layout.addWidget(self.chat_app)

    def on_connected(self):
        print("WebSocket connected")

    def on_disconnected(self):
        print("WebSocket disconnected")

    def on_textMessageReceived(self, message):
        print("Received text message:", message)

    def on_binaryMessageReceived(self, message):
        nparr = np.frombuffer(message, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, channel = img.shape
        bytesPerLine = 3 * width
        qImg = QImage(img.data, width, height,
                      bytesPerLine, QImage.Format_RGB888)
        self.camera_view.setPixmap(QPixmap.fromImage(qImg))

    def on_error(self, error_code):
        error_string = self.websocket.closeReason()
        print("WebSocket error:", error_string)


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
