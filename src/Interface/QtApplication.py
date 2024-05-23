from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ChatApplication import ChatApplication
import numpy as np
import cv2
import asyncio
import websockets
import sys
from qasync import QEventLoop


class VideoStreanmClient:
    def __init__(self, label):
        self.label = label
        self.running = True
        self.loop = asyncio.get_event_loop()

    async def receive_video(self):
        uri = 'ws://localhost:8084'
        print(f"Connecting to video server at {uri}")
        while self.running:
            try:
                print("Connecting to video server")
                async with websockets.connect(uri) as websocket:
                    while self.running:
                        print("Receiving video")
                        try:
                            data = await websocket.recv()
                            nparr = np.frombuffer(data, np.uint8)
                            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            h, w, ch = image.shape
                            bytes_per_line = ch * w
                            qt_image = QImage(image.data, w, h,
                                              bytes_per_line, QImage.Format_RGB888)
                            pixmap = QPixmap.fromImage(qt_image)
                            self.label.setPixmap(pixmap)
                            print("Video received")
                        except websockets.ConnectionClosed:
                            break
                        except Exception as e:
                            print(f"Error receiving video: {e}")
            except Exception as e:
                print(f"Error connecting to video server: {e}")
                await asyncio.sleep(1)

    def start(self):
        self.loop.run_until_complete(self.receive_video())

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi Aplicación")

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.layout = QVBoxLayout(self.widget)

        # self.web_view = QWebEngineView()
        # self.web_view.load(QUrl("http://localhost:5173/"))
        # self.layout.addWidget(self.web_view)

        self.chat_app = ChatApplication()
        self.layout.addWidget(self.chat_app)

        self.video_stream = QLabel(self)
        self.layout.addWidget(self.video_stream)

        self.camera_view = VideoStreanmClient(self.video_stream)
        self.camera_view.start()

    def closeEvent(self, event):
        # self.event_service_process.kill()
        self.camera_view.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
