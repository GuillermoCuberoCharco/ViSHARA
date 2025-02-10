from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QFrame
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, pyqtSlot, pyqtSignal
from config import WEB_URL

class LoadingIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        layout.addWidget(self.progress)
        
        self.status_label = QLabel("Cargando página...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(self.status_label)

class EnhancedWebView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWebEngineView {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
            }
        """)
        
    def createWindow(self, _):
        new_web_view = EnhancedWebView(self)
        new_web_view.urlChanged.connect(self.handle_popup)
        return new_web_view
        
    def handle_popup(self, url):
        self.setUrl(url)
        self.sender().deleteLater()

class WebViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = EnhancedWebView()
        self.browser.setUrl(QUrl(WEB_URL))
        self.loading_indicator = LoadingIndicator()
        self.browser.loadProgress.connect(self.update_loading_progress)
        self.browser.loadFinished.connect(self.handle_load_finished)
        self.browser.loadStarted.connect(self.handle_load_started)
        
        container_layout.addWidget(self.browser)
        layout.addWidget(container)
        layout.addWidget(self.loading_indicator)
        
    @pyqtSlot(int)
    def update_loading_progress(self, progress):
        self.loading_indicator.progress.setValue(progress)
        self.loading_indicator.status_label.setText(f"Cargando página... {progress}%")
        
    @pyqtSlot()
    def handle_load_started(self):
        self.loading_indicator.setVisible(True)
        self.loading_indicator.progress.setValue(0)
        self.loading_indicator.status_label.setText("Iniciando carga...")
        
    @pyqtSlot(bool)
    def handle_load_finished(self, success):
        if success:
            self.loading_indicator.status_label.setText("Carga completada")
        else:
            self.loading_indicator.status_label.setText("Error al cargar la página")
            self.loading_indicator.status_label.setStyleSheet("color: #e74c3c;")
        
        self.loading_indicator.setVisible(False)