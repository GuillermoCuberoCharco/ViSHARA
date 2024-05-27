import sys
import base64
import cv2
import numpy as np
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QGridLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QUrl
from ChatApplication import ChatApplication
from WSVideoStream import WebSocketClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wizard of Oz")
        self.label = QLabel(self)
        self.layout = QVBoxLayout()

        self.websocket_client = WebSocketClient()
        self.websocket_client.message_received.connect(
            self.on_binary_message_received)
        self.websocket_client.start()

        self.chat_app = ChatApplication()

        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("http://localhost:5173"))

        self.layout = QGridLayout()

        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.web_view, 0, 1)
        self.layout.addWidget(self.chat_app, 1, 0, 1, 2)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def on_binary_message_received(self, message):
        try:
            decoded_data = base64.b64decode(message)
            nparr = np.frombuffer(decoded_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_np is not None:
                height, width, channel = img_np.shape
                bytes_per_line = 3 * width
                q_img = QImage(img_np.data, width, height,
                               bytes_per_line, QImage.Format_BGR888)
                self.label.setPixmap(QPixmap.fromImage(q_img))
            else:
                print("Error decoding the image")
        except Exception as e:
            print(f"Error processing the image: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
