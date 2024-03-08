from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebSockets import QWebSocket
from ChatApplication import ChatApplication


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

        chat_app = ChatApplication()
        layout.addWidget(chat_app)

        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_connected)
        self.websocket.binaryMessageReceived.connect(self.handle_response)
        self.websocket.open(QUrl("ws://localhost:8083"))

        self.camera_view = QLabel()
        layout.addWidget(self.camera_view)

    def on_connected(self):
        print('Connected to WebSocket')

    def handle_response(self, message):
        image = QImage()
        image.loadFromData(message)
        self.camera_view.setPixmap(QPixmap(image))


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
