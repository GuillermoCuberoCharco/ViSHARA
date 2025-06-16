"""
Barra de estado para SHARA Wizard
"""

from typing import Optional
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QFrame, 
                            QProgressBar, QPushButton)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from config import OperationMode, ConnectionState
from services import StateService
from utils.logger import get_logger

logger = get_logger(__name__)

class StatusIndicator(QWidget):
    """Indicador visual de estado con color y texto."""
    
    def __init__(self, label: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Indicador circular
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        layout.addWidget(self.indicator)
        
        # Texto de estado
        self.label = QLabel(label)
        self.label.setStyleSheet("color: #2c3e50; font-size: 12px;")
        layout.addWidget(self.label)
    
    def set_status(self, text: str, color: str = "#7f8c8d"):
        """
        Establece el estado mostrado.
        
        Args:
            text: Texto del estado
            color: Color del indicador
        """
        self.label.setText(text)
        self.indicator.setStyleSheet(f"color: {color}; font-size: 14px;")
    
    def set_connected(self, connected: bool = True):
        """
        Establece estado de conexión.
        
        Args:
            connected: Si está conectado
        """
        if connected:
            self.set_status("Conectado", "#2ecc71")
        else:
            self.set_status("Desconectado", "#e74c3c")
    
    def set_processing(self, processing: bool = True):
        """
        Establece estado de procesamiento.
        
        Args:
            processing: Si está procesando
        """
        if processing:
            self.set_status("Procesando...", "#f39c12")
        else:
            self.set_status("Listo", "#2ecc71")

class StatsDisplay(QWidget):
    """Display de estadísticas en tiempo real."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)
        
        # Estadísticas
        self.messages_label = QLabel("Mensajes: 0")
        self.messages_label.setStyleSheet("color: #2c3e50; font-size: 11px;")
        layout.addWidget(self.messages_label)
        
        self.sessions_label = QLabel("Sesiones: 0")
        self.sessions_label.setStyleSheet("color: #2c3e50; font-size: 11px;")
        layout.addWidget(self.sessions_label)
        
        self.users_label = QLabel("Usuarios: 0")
        self.users_label.setStyleSheet("color: #2c3e50; font-size: 11px;")
        layout.addWidget(self.users_label)
    
    def update_stats(self, messages: int = 0, sessions: int = 0, users: int = 0):
        """
        Actualiza las estadísticas mostradas.
        
        Args:
            messages: Número de mensajes
            sessions: Número de sesiones
            users: Número de usuarios
        """
        self.messages_label.setText(f"Mensajes: {messages}")
        self.sessions_label.setText(f"Sesiones: {sessions}")
        self.users_label.setText(f"Usuarios: {users}")

class UserDisplay(QWidget):
    """Display de información del usuario actual."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Etiqueta
        label = QLabel("Usuario:")
        label.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: bold;")
        layout.addWidget(label)
        
        # Información del usuario
        self.user_info = QLabel("Ninguno")
        self.user_info.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.user_info)
    
    def set_user(self, user_name: Optional[str] = None, user_id: Optional[str] = None):
        """
        Establece la información del usuario.
        
        Args:
            user_name: Nombre del usuario
            user_id: ID del usuario
        """
        if user_name and user_id:
            self.user_info.setText(f"{user_name} ({user_id})")
            self.user_info.setStyleSheet("color: #2c3e50; font-size: 12px;")
        elif user_id:
            self.user_info.setText(f"Usuario {user_id}")
            self.user_info.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        else:
            self.user_info.setText("Ninguno")
            self.user_info.setStyleSheet("color: #7f8c8d; font-size: 12px;")

class ModeDisplay(QWidget):
    """Display del modo de operación actual."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Etiqueta
        label = QLabel("Modo:")
        label.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: bold;")
        layout.addWidget(label)
        
        # Modo actual
        self.mode_label = QLabel("Manual")
        self.mode_label.setStyleSheet("color: #2980b9; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.mode_label)
    
    def set_mode(self, mode: OperationMode):
        """
        Establece el modo mostrado.
        
        Args:
            mode: Modo de operación
        """
        if mode == OperationMode.AUTOMATIC:
            self.mode_label.setText("Automático")
            self.mode_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
        else:
            self.mode_label.setText("Manual")
            self.mode_label.setStyleSheet("color: #2980b9; font-size: 12px; font-weight: bold;")

class StatusBar(QWidget):
    """
    Barra de estado principal que muestra información del sistema.
    """
    
    def __init__(self, state_service: StateService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.state_service = state_service
        
        # Componentes
        self.connection_indicator = None
        self.processing_indicator = None
        self.stats_display = None
        self.user_display = None
        self.mode_display = None
        self.status_message = None
        
        # Timer para actualización de estadísticas
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(5000)  # Actualizar cada 5 segundos
        
        self._setup_ui()
        self._connect_signals()
        
        logger.debug("StatusBar inicializada")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        self.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-top: 1px solid #bdc3c7;
                padding: 2px;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(15)
        
        # Indicadores de estado
        self._setup_status_indicators(main_layout)
        
        # Separador
        separator1 = self._create_separator()
        main_layout.addWidget(separator1)
        
        # Información del usuario
        self.user_display = UserDisplay()
        main_layout.addWidget(self.user_display)
        
        # Separador
        separator2 = self._create_separator()
        main_layout.addWidget(separator2)
        
        # Modo de operación
        self.mode_display = ModeDisplay()
        main_layout.addWidget(self.mode_display)
        
        # Separador
        separator3 = self._create_separator()
        main_layout.addWidget(separator3)
        
        # Estadísticas
        self.stats_display = StatsDisplay()
        main_layout.addWidget(self.stats_display)
        
        # Espaciador
        main_layout.addStretch()
        
        # Mensaje de estado
        self.status_message = QLabel("Iniciando...")
        self.status_message.setStyleSheet("color: #2c3e50; font-size: 12px;")
        main_layout.addWidget(self.status_message)
        
        logger.debug("UI de barra de estado configurada")
    
    def _setup_status_indicators(self, parent_layout):
        """Configura los indicadores de estado."""
        # Indicador de conexión
        self.connection_indicator = StatusIndicator("Desconectado")
        parent_layout.addWidget(self.connection_indicator)
        
        # Indicador de procesamiento
        self.processing_indicator = StatusIndicator("Inactivo")
        parent_layout.addWidget(self.processing_indicator)
    
    def _create_separator(self) -> QFrame:
        """Crea un separador vertical."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #bdc3c7;")
        return separator
    
    def _connect_signals(self):
        """Conecta las señales del servicio de estado."""
        self.state_service.connection_state_changed.connect(self._on_connection_changed)
        self.state_service.operation_mode_changed.connect(self._on_mode_changed)
        self.state_service.current_user_changed.connect(self._on_user_changed)
        self.state_service.app_status_changed.connect(self._on_status_changed)
        
        logger.debug("Señales de barra de estado conectadas")
    
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        """Maneja cambios en el estado de conexión."""
        self.connection_indicator.set_connected(connected)
        
        if connected:
            self.processing_indicator.set_status("Listo", "#2ecc71")
        else:
            self.processing_indicator.set_status("Desconectado", "#e74c3c")
    
    @pyqtSlot(object)
    def _on_mode_changed(self, mode: OperationMode):
        """Maneja cambios en el modo de operación."""
        self.mode_display.set_mode(mode)
    
    @pyqtSlot(object)
    def _on_user_changed(self, user):
        """Maneja cambios en el usuario actual."""
        if user:
            self.user_display.set_user(user.user_name, user.user_id)
        else:
            self.user_display.set_user()
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """Maneja cambios en el estado de la aplicación."""
        self.status_message.setText(status)
        
        # Actualizar indicador de procesamiento
        if "procesando" in status.lower() or "processing" in status.lower():
            self.processing_indicator.set_processing(True)
        elif "listo" in status.lower() or "ready" in status.lower():
            self.processing_indicator.set_processing(False)
    
    def _update_stats(self):
        """Actualiza las estadísticas mostradas."""
        try:
            stats = self.state_service.get_stats()
            
            self.stats_display.update_stats(
                messages=stats.get('messages_sent', 0) + stats.get('messages_received', 0),
                sessions=stats.get('sessions_created', 0),
                users=stats.get('users_detected', 0)
            )
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def set_processing_status(self, processing: bool, message: str = ""):
        """
        Establece el estado de procesamiento.
        
        Args:
            processing: Si está procesando
            message: Mensaje adicional
        """
        self.processing_indicator.set_processing(processing)
        
        if message:
            self.status_message.setText(message)
    
    def show_temporary_message(self, message: str, duration: int = 3000):
        """
        Muestra un mensaje temporal.
        
        Args:
            message: Mensaje a mostrar
            duration: Duración en milisegundos
        """
        original_message = self.status_message.text()
        self.status_message.setText(message)
        
        # Restaurar mensaje original después del tiempo especificado
        QTimer.singleShot(
            duration, 
            lambda: self.status_message.setText(original_message)
        )
    
    def update_connection_info(self, server_url: str, connected: bool):
        """
        Actualiza información de conexión.
        
        Args:
            server_url: URL del servidor
            connected: Estado de conexión
        """
        if connected:
            self.connection_indicator.set_status(f"Conectado a {server_url}", "#2ecc71")
        else:
            self.connection_indicator.set_status("Desconectado", "#e74c3c")
    
    def flash_indicator(self, indicator_type: str = "processing"):
        """
        Hace parpadear un indicador.
        
        Args:
            indicator_type: Tipo de indicador ('connection' o 'processing')
        """
        if indicator_type == "connection":
            indicator = self.connection_indicator.indicator
        else:
            indicator = self.processing_indicator.indicator
        
        # Guardar estilo original
        original_style = indicator.styleSheet()
        
        # Cambiar a color de flash
        indicator.setStyleSheet("color: #f39c12; font-size: 14px;")
        
        # Restaurar después de 200ms
        QTimer.singleShot(200, lambda: indicator.setStyleSheet(original_style))
    
    def get_current_status(self) -> dict:
        """
        Obtiene el estado actual de todos los componentes.
        
        Returns:
            Diccionario con el estado actual
        """
        return {
            'connection_status': self.connection_indicator.label.text(),
            'processing_status': self.processing_indicator.label.text(),
            'current_user': self.user_display.user_info.text(),
            'operation_mode': self.mode_display.mode_label.text(),
            'status_message': self.status_message.text()
        }
    
    async def cleanup(self):
        """Limpia recursos de la barra de estado."""
        try:
            logger.info("Limpiando barra de estado...")
            
            # Detener timer
            self.stats_timer.stop()
            
            logger.info("Barra de estado limpiada")
            
        except Exception as e:
            logger.error(f"Error limpiando barra de estado: {e}")
    
    def reset_display(self):
        """Reinicia el display a valores por defecto."""
        self.connection_indicator.set_status("Desconectado", "#e74c3c")
        self.processing_indicator.set_status("Inactivo", "#7f8c8d")
        self.user_display.set_user()
        self.mode_display.set_mode(OperationMode.MANUAL)
        self.stats_display.update_stats(0, 0, 0)
        self.status_message.setText("Iniciando...")
        
        logger.debug("Display de barra de estado reiniciado")