import sys
import asyncio
import qasync
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter, QWidget
from PyQt6.QtCore import Qt
from ChatApplication import ChatApplication
from WebView import WebViewWidget
# from WebRTCClient import WebRTCClient, WebRTCThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        self.chat_app = ChatApplication()
        splitter.addWidget(self.chat_app)

        self.web_view = WebViewWidget()
        splitter.addWidget(self.web_view)

        web_container = QWidget()
        web_layout = QVBoxLayout(web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)

        splitter.setSizes([self.width() // 2, self.width() // 2])

        self.setWindowTitle('Wizard of Oz Chat App')
        self.setGeometry(100, 100, 1200, 800)

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