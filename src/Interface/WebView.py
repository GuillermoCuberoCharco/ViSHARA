from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

class WebViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        self.browser.load(QUrl("http://localhost:5173"))