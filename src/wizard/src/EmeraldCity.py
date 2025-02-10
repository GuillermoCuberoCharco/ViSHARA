import sys
import asyncio
import qasync
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter, QFrame, QLabel, QPushButton, QStyle, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from ChatApplication import ChatApplication
from WebView import WebViewWidget
from CameraTracker import CameraWidget

class StyledFrame(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
        """)
        
        if title:
            self.header = QLabel(title)
            self.header.setStyleSheet("""
                QLabel {
                    background-color: #2c3e50;
                    color: white;
                    padding: 2px 8px;
                    font-weight: bold;
                    border-top-left-radius: 7px;
                    border-top-right-radius: 7px;
                    min_height: 10px;
                }
            """)
            self.main_layout.addWidget(self.header)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addWidget(self.content)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

       # Chat section (left side)
        chat_frame = StyledFrame("Operator Chat Interface")
        self.chat_app = ChatApplication()
        chat_frame.content_layout.addWidget(self.chat_app)
        main_splitter.addWidget(chat_frame)

        # Right side container
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Right vertical splitter
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_layout.addWidget(right_splitter)

        # Camera section
        camera_frame = StyledFrame("User Camera Feed")
        self.camera_widget = CameraWidget()
        camera_frame.content_layout.addWidget(self.camera_widget)
        right_splitter.addWidget(camera_frame)

        # Web view section
        web_frame = StyledFrame("User Web Interface")
        self.web_view = WebViewWidget()
        web_frame.content_layout.addWidget(self.web_view)
        right_splitter.addWidget(web_frame)

        # Add right side to main splitter
        main_splitter.addWidget(right_widget)

        # Set initial sizes
        # Chat ocupa 40% del ancho, el lado derecho 60%
        main_splitter.setSizes([40 * self.width() // 100, 60 * self.width() // 100])
        
        # Cámara ocupa 40% del alto del lado derecho, web app 60%
        right_splitter.setSizes([40 * self.height() // 100, 60 * self.height() // 100])

        self.setWindowTitle('Wizard of Oz Interface')
        self.setGeometry(100, 100, 1400, 900)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QSplitter::handle {
                background-color: #cccccc;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            StyledFrame {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #cccccc;
            }
        """)

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