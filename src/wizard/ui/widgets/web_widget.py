"""
Widget web para SHARA Wizard
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QFrame, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont

from config import settings
from services import StateService
from utils.logger import get_logger

logger = get_logger(__name__)

class LoadingIndicator(QFrame):
    """Indicador de carga para la página web."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Estilos del frame
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Barra de progreso
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        layout.addWidget(self.progress)
        
        # Label de estado
        self.status_label = QLabel("Cargando página...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #2c3e50; font-size: 12px;")
        layout.addWidget(self.status_label)
    
    def update_progress(self, progress: int):
        """
        Actualiza el progreso de carga.
        
        Args:
            progress: Progreso de 0 a 100
        """
        self.progress.setValue(progress)
        self.status_label.setText(f"Cargando página... {progress}%")
    
    def set_status(self, status: str, is_error: bool = False):
        """
        Establece el estado mostrado.
        
        Args:
            status: Mensaje de estado
            is_error: Si es un mensaje de error
        """
        self.status_label.setText(status)
        
        if is_error:
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        else:
            self.status_label.setStyleSheet("color: #2c3e50; font-size: 12px;")

class EnhancedWebView(QWebEngineView):
    """Vista web mejorada con manejo de ventanas emergentes."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Estilos
        self.setStyleSheet("""
            QWebEngineView {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
            }
        """)
    
    def createWindow(self, window_type):
        """
        Maneja la creación de ventanas emergentes.
        
        Args:
            window_type: Tipo de ventana
            
        Returns:
            Nueva vista web
        """
        new_web_view = EnhancedWebView(self)
        new_web_view.urlChanged.connect(self.handle_popup)
        return new_web_view
    
    def handle_popup(self, url: QUrl):
        """
        Maneja ventanas emergentes redirigiendo a la ventana principal.
        
        Args:
            url: URL de la ventana emergente
        """
        self.setUrl(url)
        self.sender().deleteLater()

class ConnectionStatus(QWidget):
    """Widget de estado de conexión web."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Indicador de estado
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #e74c3c; font-size: 16px;")
        layout.addWidget(self.status_indicator)
        
        # Texto de estado
        self.status_text = QLabel("Desconectado")
        self.status_text.setStyleSheet("color: #2c3e50; font-size: 12px;")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        
        # URL actual
        self.url_label = QLabel("")
        self.url_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        self.url_label.setWordWrap(True)
        layout.addWidget(self.url_label)
    
    def update_status(self, connected: bool, status_text: str = ""):
        """
        Actualiza el estado de conexión.
        
        Args:
            connected: Si está conectado
            status_text: Texto de estado adicional
        """
        if connected:
            self.status_indicator.setStyleSheet("color: #2ecc71; font-size: 16px;")
            self.status_text.setText("Conectado")
        else:
            self.status_indicator.setStyleSheet("color: #e74c3c; font-size: 16px;")
            self.status_text.setText("Desconectado")
        
        if status_text:
            self.status_text.setText(status_text)
    
    def update_url(self, url: str):
        """
        Actualiza la URL mostrada.
        
        Args:
            url: URL actual
        """
        # Truncar URL si es muy larga
        if len(url) > 50:
            url = url[:47] + "..."
        self.url_label.setText(url)

class WebWidget(QWidget):
    """
    Widget que muestra la interfaz web del usuario usando QWebEngineView.
    """
    
    def __init__(self, state_service: StateService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.state_service = state_service
        
        # Estado del widget
        self.is_loaded = False
        self.load_attempts = 0
        self.max_load_attempts = 3
        
        # Componentes UI
        self.browser = None
        self.loading_indicator = None
        self.connection_status = None
        
        # Timer para reintentos
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self._retry_load)
        self.retry_timer.setSingleShot(True)
        
        self._setup_ui()
        self._load_web_page()
        
        logger.debug("WebWidget inicializado")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Frame contenedor principal
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
        
        # Vista web
        self.browser = EnhancedWebView()
        container_layout.addWidget(self.browser)
        
        layout.addWidget(container)
        
        # Indicador de carga
        self.loading_indicator = LoadingIndicator()
        layout.addWidget(self.loading_indicator)
        
        # Estado de conexión
        self.connection_status = ConnectionStatus()
        layout.addWidget(self.connection_status)
        
        # Conectar señales
        self._connect_browser_signals()
        
        logger.debug("UI web configurada")

    def _setup_synchronization(self):
        """Configura la sincronización como cliente operator."""
        try:
            js_sync_code: f"""
            (function() {{
                console.log('Configurando cliente operator...');
                
                // Verificar si ya existe conexión
                if (window.operatorSocket && window.operatorSocket.connected) {{
                    console.log('Socket operator ya conectado');
                    return;
                }}
                
                // Crear conexión WebSocket como operator
                if (typeof io !== 'undefined') {{
                    window.operatorSocket = io('{settings.server.url}');
                    
                    window.operatorSocket.on('connect', () => {{
                        console.log('operator socket conectado');
                        
                        // Registrarse como cliente operator
                        window.operatorSocket.emit('register_client', {{
                            client: 'web',
                            type: 'operator',
                            source: 'wizard_app',
                            timestamp: Date.now()
                        }});
                    }});
                    
                    window.operatorSocket.on('registration_success', (data) => {{
                        console.log('operator registrado exitosamente:', data);
                    }});
                    
                    // Handlers de sincronización
                    window.operatorSocket.on('ui_state_sync', (data) => {{
                        console.log('Sincronizando estado UI:', data);
                        if (window.syncUIState) {{
                            window.syncUIState(data);
                        }}
                    }});
                    
                    window.operatorSocket.on('conversation_scroll_sync', (data) => {{
                        console.log('Sincronizando scroll:', data);
                        if (window.syncConversationScroll) {{
                            window.syncConversationScroll(data);
                        }}
                    }});
                    
                    window.operatorSocket.on('robot_animation_sync', (data) => {{
                        console.log('Sincronizando animación:', data);
                        if (window.syncRobotAnimation) {{
                            window.syncRobotAnimation(data);
                        }}
                    }});
                    
                    window.operatorSocket.on('disconnect', () => {{
                        console.log('operator socket desconectado');
                    }});
                    
                }} else {{
                    console.error('Socket.IO no está disponible');
                    setTimeout(() => window.setupOperatorSync(), 2000);
                }}
            }})();
            """

            self.browser.page().runJavaScript(js_sync_code)
            logger.info("Sincronización configurada como cliente operator")
        except Exception as e:
            logger.error(f"Error configurando sincronización: {e}")
    
    def _connect_browser_signals(self):
        """Conecta las señales del navegador."""
        self.browser.loadProgress.connect(self.update_loading_progress)
        self.browser.loadFinished.connect(self.handle_load_finished)
        self.browser.loadStarted.connect(self.handle_load_started)
        self.browser.urlChanged.connect(self._on_url_changed)
        
        logger.debug("Señales del navegador conectadas")
    
    def _load_web_page(self):
        """Carga la página web configurada."""
        try:
            web_url = settings.server.web_url
            logger.info(f"Cargando página web: {web_url}")
            
            self.browser.setUrl(QUrl(web_url))
            self.connection_status.update_url(web_url)
            
        except Exception as e:
            logger.error(f"Error cargando página web: {e}")
            self._show_error_page(f"Error cargando página: {str(e)}")
    
    @pyqtSlot(int)
    def update_loading_progress(self, progress: int):
        """
        Actualiza el progreso de carga.
        
        Args:
            progress: Progreso de 0 a 100
        """
        self.loading_indicator.update_progress(progress)
        self.connection_status.update_status(
            False, 
            f"Cargando... {progress}%"
        )
    
    @pyqtSlot()
    def handle_load_started(self):
        """Maneja el inicio de carga."""
        self.loading_indicator.setVisible(True)
        self.loading_indicator.update_progress(0)
        self.loading_indicator.set_status("Iniciando carga...")
        self.connection_status.update_status(False, "Cargando...")
        
        logger.debug("Inicio de carga de página web")
    
    @pyqtSlot(bool)
    def handle_load_finished(self, success: bool):
        """
        Maneja la finalización de carga.
        
        Args:
            success: Si la carga fue exitosa
        """
        if success:
            self.is_loaded = True
            self.load_attempts = 0
            self.loading_indicator.set_status("Carga completada")
            self.connection_status.update_status(True, "Página cargada")

            QTimer.singleShot(3000, self._setup_synchronization)
            
            logger.info("Página web cargada exitosamente")
        else:
            self.is_loaded = False
            self.load_attempts += 1
            
            error_msg = f"Error al cargar la página (intento {self.load_attempts})"
            self.loading_indicator.set_status(error_msg, is_error=True)
            self.connection_status.update_status(False, error_msg)
            
            logger.error(f"Error cargando página web: {error_msg}")
            
            # Reintentar si no se ha alcanzado el máximo
            if self.load_attempts < self.max_load_attempts:
                retry_delay = 5000 * self.load_attempts  # Delay incremental
                self.retry_timer.start(retry_delay)
                
                retry_msg = f"Reintentando en {retry_delay//1000} segundos..."
                self.loading_indicator.set_status(retry_msg)
            else:
                self._show_error_page("No se pudo cargar la página después de varios intentos")
        
        # Ocultar indicador de carga después de un momento
        QTimer.singleShot(2000, lambda: self.loading_indicator.setVisible(False))
    
    def _on_url_changed(self, url: QUrl):
        """
        Maneja el cambio de URL.
        
        Args:
            url: Nueva URL
        """
        url_string = url.toString()
        self.connection_status.update_url(url_string)
        logger.debug(f"URL cambiada a: {url_string}")
    
    def _retry_load(self):
        """Reintenta cargar la página."""
        logger.info(f"Reintentando carga de página (intento {self.load_attempts + 1})")
        self._load_web_page()
    
    def _show_error_page(self, error_message: str):
        """
        Muestra una página de error.
        
        Args:
            error_message: Mensaje de error a mostrar
        """
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error de Carga</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f8f9fa;
                }}
                .error-container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .error-icon {{
                    font-size: 48px;
                    color: #e74c3c;
                    margin-bottom: 20px;
                }}
                .error-title {{
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .error-message {{
                    color: #7f8c8d;
                    margin-bottom: 20px;
                }}
                .retry-button {{
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h2 class="error-title">No se pudo cargar la página</h2>
                <p class="error-message">{error_message}</p>
                <button class="retry-button" onclick="location.reload()">Reintentar</button>
            </div>
        </body>
        </html>
        """
        
        self.browser.setHtml(error_html)
        self.connection_status.update_status(False, "Error de carga")
    
    def reload_page(self):
        """Recarga la página actual."""
        self.load_attempts = 0
        self.browser.reload()
        logger.info("Recargando página web")
    
    def navigate_to_url(self, url: str):
        """
        Navega a una URL específica.
        
        Args:
            url: URL a la que navegar
        """
        try:
            self.browser.setUrl(QUrl(url))
            logger.info(f"Navegando a: {url}")
        except Exception as e:
            logger.error(f"Error navegando a {url}: {e}")
    
    def navigate_home(self):
        """Navega a la página principal configurada."""
        self._load_web_page()
    
    def stop_loading(self):
        """Detiene la carga actual."""
        self.browser.stop()
        self.retry_timer.stop()
        logger.debug("Carga de página detenida")
    
    def get_current_url(self) -> str:
        """
        Obtiene la URL actual.
        
        Returns:
            URL actual como string
        """
        return self.browser.url().toString()
    
    def is_page_loaded(self) -> bool:
        """
        Verifica si la página está cargada.
        
        Returns:
            True si la página está cargada
        """
        return self.is_loaded
    
    async def cleanup(self):
        """Limpia recursos del widget."""
        try:
            logger.info("Limpiando widget web...")
            
            # Detener timers
            self.retry_timer.stop()
            
            # Detener carga si está en progreso
            if self.browser:
                self.browser.stop()
            
            logger.info("Widget web limpiado")
            
        except Exception as e:
            logger.error(f"Error limpiando widget web: {e}")
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del widget.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'is_loaded': self.is_loaded,
            'load_attempts': self.load_attempts,
            'max_load_attempts': self.max_load_attempts,
            'current_url': self.get_current_url(),
            'configured_url': settings.server.web_url
        }
    
    # Métodos de control externos
    def show_loading_indicator(self, show: bool = True):
        """Muestra u oculta el indicador de carga."""
        self.loading_indicator.setVisible(show)
    
    def set_zoom_factor(self, factor: float):
        """
        Establece el factor de zoom de la página.
        
        Args:
            factor: Factor de zoom (1.0 = 100%)
        """
        self.browser.setZoomFactor(factor)
        logger.debug(f"Factor de zoom establecido a: {factor}")
    
    def execute_javascript(self, script: str):
        """
        Ejecuta JavaScript en la página.
        
        Args:
            script: Código JavaScript a ejecutar
        """
        try:
            self.browser.page().runJavaScript(script)
            logger.debug("JavaScript ejecutado")
        except Exception as e:
            logger.error(f"Error ejecutando JavaScript: {e}")