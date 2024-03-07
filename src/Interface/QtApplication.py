from PyQt5.QtCore import QUrl, QByteArray, QBuffer, QIODevice, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
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

        self.camera_view = QLabel()
        layout.addWidget(self.camera_view)


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
