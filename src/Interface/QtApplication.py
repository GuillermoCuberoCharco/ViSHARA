import sys
import asyncio
import qasync
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter, QWidget
from PyQt6.QtCore import Qt
from ChatApplication import ChatApplication
from WebView import WebViewWidget
from CameraTracker import CameraWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_layout.addWidget(left_splitter)

        self.chat_app = ChatApplication()
        left_splitter.addWidget(self.chat_app)

        self.camera_widget = CameraWidget()
        left_splitter.addWidget(self.camera_widget)

        main_splitter.addWidget(left_widget)

        self.web_view = WebViewWidget()
        main_splitter.addWidget(self.web_view)

        height = self.height()
        left_splitter.setSizes([int(height * 0.7), int(height * 0.3)])
        main_splitter.setSizes([self.width() // 2, self.width() // 2])

        self.setWindowTitle('Wizard of Oz Chat App')
        self.setGeometry(100, 100, 1200, 800)

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
        await main_window.camera_widget.cleanup()

if __name__ == '__main__':
    qasync.run(main())