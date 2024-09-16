import sys
import numpy as np
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QGridLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QUrl, pyqtSlot
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

        

    @pyqtSlot(bytes)
    def on_frame_recived(self, frame_data):
        img_np = np.frombuffer(frame_data, dtype=np.uint8).reshape((480, 640, 3))
        height, width, channel = img_np.shape
        bytes_per_line = 3 * width
        q_img = QImage(img_np.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
