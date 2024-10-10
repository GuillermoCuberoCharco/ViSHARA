import sys
import asyncio
import qasync
from qasync import QEventLoop
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter
from ChatApplication import ChatApplication
from WebRTCClient import WebRTCClient, WebRTCThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        self.chat_app = ChatApplication()
        splitter.addWidget(self.chat_app)

        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("http://localhost:5173"))
        splitter.addWidget(self.web_view)

        splitter.setSizes([300, 300])

        self.setWindowTitle('Wizard of Oz Chat App')
        self.setGeometry(100, 100, 1000, 600)

        # self.webrtc_client = WebRTCClient()
        # self.webrtc_client.frame_received.connect(self.on_frame_recived)
        # self.webrtc_thread = WebRTCThread(self.webrtc_client)
        # self.webrtc_thread.start()

async def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    main_window = MainWindow()
    main_window.show()

    await main_window.chat_app.initialize()

    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    future = asyncio.Future()

    app.lastWindowClosed.connect(lambda: close_future(future, loop))

    try:
        await future
    except asyncio.CancelledError:
        pass
    finally:
        await main_window.chat_app.close_application()

if __name__ == '__main__':
    qasync.run(main())