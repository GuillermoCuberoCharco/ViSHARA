"""
Aplicación principal SHARA Wizard of Oz Interface
"""

import asyncio
from typing import Optional
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal

from config import settings, WINDOW_GEOMETRY, SPLITTER_RATIOS
from core.event_manager import EventManager
from services.socket_service import SocketService
from services.message_service import MessageService
from services.video_service import VideoService
from services.state_service import StateService
from ui.main_window import MainWindow
from utils.logger import get_logger

logger = get_logger(__name__)

class SharaWizardApp(QMainWindow):
    """
    Aplicación principal del Wizard of Oz para SHARA.
    
    Coordina todos los servicios y componentes de la interfaz.
    """
    
    # Señales
    initialized = pyqtSignal()
    closing = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Servicios principales
        self.event_manager = EventManager()
        self.state_service = StateService(self.event_manager)
        self.socket_service = SocketService(self.event_manager)
        self.message_service = MessageService(self.event_manager, self.socket_service)
        self.video_service = VideoService(self.event_manager, self.socket_service)
        
        # Interfaz de usuario
        self.main_window = None
        self.is_initialized = False
        
        self._setup_ui()
        self._connect_signals()
        
        logger.info("SharaWizardApp creada")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario principal."""
        # Configurar ventana principal
        self.setWindowTitle(settings.ui.window_title)
        self.setGeometry(100, 100, settings.ui.window_width, settings.ui.window_height)
        self.setMinimumSize(WINDOW_GEOMETRY['MIN_WIDTH'], WINDOW_GEOMETRY['MIN_HEIGHT'])
        
        # Crear y configurar la ventana principal
        self.main_window = MainWindow(
            event_manager=self.event_manager,
            message_service=self.message_service,
            video_service=self.video_service,
            state_service=self.state_service
        )
        
        self.setCentralWidget(self.main_window)
        
        # Aplicar estilos
        self._apply_styles()
        
        logger.debug("UI configurada")
    
    def _apply_styles(self):
        """Aplica los estilos globales a la aplicación."""
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
        """)
    
    def _connect_signals(self):
        """Conecta las señales de los servicios."""
        # Conectar señales de eventos
        self.event_manager.subscribe('app_initialized', self._on_app_initialized)
        self.event_manager.subscribe('app_closing', self._on_app_closing)
        
        # Conectar señales de servicios
        self.socket_service.connection_established.connect(self._on_connection_established)
        self.socket_service.connection_lost.connect(self._on_connection_lost)
        
        logger.debug("Señales conectadas")
    
    async def initialize(self):
        """
        Inicializa todos los servicios de la aplicación de forma asíncrona.
        """
        if self.is_initialized:
            logger.warning("La aplicación ya está inicializada")
            return
        
        try:
            logger.info("Inicializando servicios...")
            
            # Inicializar servicios en orden
            await self.socket_service.initialize()
            await self.message_service.initialize()
            await self.video_service.initialize()
            
            # Marcar como inicializada
            self.is_initialized = True
            
            # Emitir evento de inicialización
            self.event_manager.emit('app_initialized')
            self.initialized.emit()
            
            logger.info("Aplicación inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando la aplicación: {e}")
            raise
    
    async def cleanup(self):
        """
        Limpia todos los recursos de forma asíncrona.
        """
        if not self.is_initialized:
            return
        
        try:
            logger.info("Cerrando aplicación...")
            
            # Emitir evento de cierre
            self.event_manager.emit('app_closing')
            self.closing.emit()
            
            # Limpiar servicios en orden inverso
            await self.video_service.cleanup()
            await self.message_service.cleanup()
            await self.socket_service.cleanup()
            
            # Limpiar UI
            if self.main_window:
                await self.main_window.cleanup()
            
            self.is_initialized = False
            
            logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            logger.error(f"Error cerrando la aplicación: {e}")
    
    def _on_app_initialized(self):
        """Maneja el evento de aplicación inicializada."""
        logger.debug("Aplicación inicializada - evento procesado")
    
    def _on_app_closing(self):
        """Maneja el evento de cierre de aplicación."""
        logger.debug("Aplicación cerrándose - evento procesado")
    
    def _on_connection_established(self):
        """Maneja el evento de conexión establecida."""
        logger.info("Conexión establecida con el servidor")
        self.state_service.set_connection_state(True)
    
    def _on_connection_lost(self):
        """Maneja el evento de conexión perdida."""
        logger.warning("Conexión perdida con el servidor")
        self.state_service.set_connection_state(False)
    
    def closeEvent(self, event):
        """
        Maneja el evento de cierre de ventana.
        """
        # Crear tarea para limpiar de forma asíncrona
        if self.is_initialized:
            asyncio.create_task(self.cleanup())
        
        event.accept()
        super().closeEvent(event)
    
    def showEvent(self, event):
        """Maneja el evento de mostrar ventana."""
        super().showEvent(event)
        logger.debug("Ventana principal mostrada")
    
    def get_service(self, service_name: str):
        """
        Obtiene una referencia a un servicio específico.
        
        Args:
            service_name: Nombre del servicio ('socket', 'message', 'video', 'state')
            
        Returns:
            El servicio solicitado o None si no existe
        """
        services = {
            'socket': self.socket_service,
            'message': self.message_service,
            'video': self.video_service,
            'state': self.state_service,
            'event': self.event_manager
        }
        
        return services.get(service_name)
    
    @property
    def is_connected(self) -> bool:
        """Verifica si la aplicación está conectada al servidor."""
        return self.socket_service.is_connected if self.socket_service else False
    
    @property
    def current_mode(self):
        """Obtiene el modo actual de operación."""
        return self.state_service.operation_mode if self.state_service else None