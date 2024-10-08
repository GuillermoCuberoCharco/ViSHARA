import sys
import asyncio
import qasync
from qasync import QEventLoop
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGridLayout
from ChatApplication import ChatApplication
from WebRTCClient import WebRTCClient, WebRTCThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wizard of Oz")

        self.chat_app = ChatApplication()

        # self.web_view = QWebEngineView()
        # self.web_view.load(QUrl("http://localhost:5173"))

        # self.webrtc_client = WebRTCClient()
        # self.webrtc_client.frame_received.connect(self.on_frame_recived)
        # self.webrtc_thread = WebRTCThread(self.webrtc_client)
        # self.webrtc_thread.start()

        self.layout = QGridLayout()
        # self.layout.addWidget(self.web_view, 0, 1)
        self.layout.addWidget(self.chat_app, 0, 0, 1, 1)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

async def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        await loop.run_forever()

if __name__ == "__main__":
    asyncio.run(main())