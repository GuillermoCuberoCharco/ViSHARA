"""
Ventana principal de SHARA Wizard
"""

from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QSplitter, QFrame, 
                            QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt

from config import WINDOW_GEOMETRY, SPLITTER_RATIOS
from core.event_manager import EventManager
from services import MessageService, VideoService, StateService
from ui.widgets import ChatWidget, CameraWidget, WebWidget, StatusBar
from ui.styles.theme import apply_main_window_styles
from utils.logger import get_logger

logger = get_logger(__name__)

class StyledFrame(QFrame):
    """Frame estilizado para secciones de la interfaz."""
    
    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Aplicar estilos
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
        """)
        
        # Agregar header si se proporciona título
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
                    min-height: 10px;
                }
            """)
            self.main_layout.addWidget(self.header)
        
        # Contenedor para el contenido
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addWidget(self.content)

class MainWindow(QWidget):
    """
    Ventana principal de la aplicación Wizard of Oz.
    Contiene el chat, la cámara y la vista web.
    """
    
    def __init__(self, event_manager: EventManager, message_service: MessageService,
                 video_service: VideoService, state_service: StateService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.event_manager = event_manager
        self.message_service = message_service
        self.video_service = video_service
        self.state_service = state_service
        
        # Widgets principales
        self.chat_widget = None
        self.camera_widget = None
        self.web_widget = None
        
        # Layout principal
        self.main_layout = None
        self.main_splitter = None
        self.right_splitter = None
        
        self._setup_ui()
        self._connect_signals()
        
        logger.debug("MainWindow inicializada")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Splitter principal horizontal
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Sección de chat (lado izquierdo)
        self._setup_chat_section()
        
        # Sección derecha (cámara + web)
        self._setup_right_section()
        
        # Configurar tamaños iniciales
        self._configure_splitter_sizes()
        
        # Aplicar estilos
        apply_main_window_styles(self)
        
        logger.debug("UI configurada")
    
    def _setup_chat_section(self):
        """Configura la sección de chat."""
        chat_frame = StyledFrame("Interfaz de Chat del Operador")
        
        self.chat_widget = ChatWidget(
            event_manager=self.event_manager,
            message_service=self.message_service,
            state_service=self.state_service,
            parent=chat_frame.content
        )
        
        chat_frame.content_layout.addWidget(self.chat_widget)
        self.main_splitter.addWidget(chat_frame)
        
        logger.debug("Sección de chat configurada")
    
    def _setup_right_section(self):
        """Configura la sección derecha (cámara + web)."""
        # Widget contenedor derecho
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Splitter vertical para cámara y web
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_layout.addWidget(self.right_splitter)
        
        # Sección de cámara
        self._setup_camera_section()
        
        # Sección web
        self._setup_web_section()
        
        # Agregar al splitter principal
        self.main_splitter.addWidget(right_widget)
        
        logger.debug("Sección derecha configurada")
    
    def _setup_camera_section(self):
        """Configura la sección de cámara."""
        camera_frame = StyledFrame("Feed de Cámara del Usuario")
        
        self.camera_widget = CameraWidget(
            video_service=self.video_service,
            state_service=self.state_service,
            parent=camera_frame.content
        )
        
        camera_frame.content_layout.addWidget(self.camera_widget)
        self.right_splitter.addWidget(camera_frame)
        
        logger.debug("Sección de cámara configurada")
    
    def _setup_web_section(self):
        """Configura la sección web."""
        web_frame = StyledFrame("Interfaz Web del Usuario")
        
        self.web_widget = WebWidget(
            state_service=self.state_service,
            parent=web_frame.content
        )
        
        web_frame.content_layout.addWidget(self.web_widget)
        self.right_splitter.addWidget(web_frame)
        
        logger.debug("Sección web configurada")
    
    def _configure_splitter_sizes(self):
        """Configura los tamaños iniciales de los splitters."""
        # Obtener tamaños de ventana
        window_width = WINDOW_GEOMETRY['DEFAULT_WIDTH']
        window_height = WINDOW_GEOMETRY['DEFAULT_HEIGHT']
        
        # Configurar splitter principal (horizontal)
        chat_width = int(window_width * SPLITTER_RATIOS['MAIN_HORIZONTAL'][0] / 100)
        right_width = int(window_width * SPLITTER_RATIOS['MAIN_HORIZONTAL'][1] / 100)
        self.main_splitter.setSizes([chat_width, right_width])
        
        # Configurar splitter derecho (vertical)
        camera_height = int(window_height * SPLITTER_RATIOS['RIGHT_VERTICAL'][0] / 100)
        web_height = int(window_height * SPLITTER_RATIOS['RIGHT_VERTICAL'][1] / 100)
        self.right_splitter.setSizes([camera_height, web_height])
        
        logger.debug("Tamaños de splitters configurados")
    
    def _connect_signals(self):
        """Conecta las señales entre componentes."""
        
        # Conectar señales del servicio de mensajes
        self.message_service.user_response_required.connect(self._on_user_response_required)

        self.message_service.user_response_with_states_required.connect(self._on_user_response_with_states_required)
        
        logger.debug("Señales conectadas")
    
    def _on_user_response_required(self, message, state):
        """Maneja cuando se requiere respuesta del usuario."""
        if self.chat_widget:
        # Validar el tipo de state antes de pasarlo
            if isinstance(state, dict):
                # Si state es un diccionario (ai_responses), extraer el estado del mensaje
                robot_state = message.robot_state.value if message.robot_state else 'attention'
                logger.warning(f"Se recibió diccionario como state en _on_user_response_required, usando estado del mensaje: {robot_state}")
                self.chat_widget.show_response_for_editing(message, robot_state, state)
            elif isinstance(state, str):
                # Si state es una cadena (estado del robot), usar show_response_for_editing normal
                self.chat_widget.show_response_for_editing(message, state)
            else:
                # Si state es de otro tipo, extraer estado del mensaje y usar diccionario vacío
                robot_state = message.robot_state.value if message.robot_state else 'attention'
                logger.warning(f"Tipo de state no válido en _on_user_response_required: {type(state)}, usando estado del mensaje: {robot_state}")
                self.chat_widget.show_response_for_editing(message, robot_state, {})

    def _on_user_response_with_states_required(self, message, ai_responses, user_message):
        """Maneja cuando se requiere respuesta del usuario con estados."""
        if self.chat_widget:
            if not isinstance(ai_responses, dict):
                logger.error(f"Tipo de ai_responses no válido: {type(ai_responses)}. Se esperaba dict.")
                ai_responses = {}
                
            self.chat_widget.show_response_dialog_with_states(message, ai_responses, user_message)
    async def cleanup(self):
        """Limpia recursos de la ventana principal."""
        try:
            logger.info("Limpiando ventana principal...")
            
            # Limpiar widgets
            if self.chat_widget:
                await self.chat_widget.cleanup()
            
            if self.camera_widget:
                await self.camera_widget.cleanup()
            
            if self.web_widget:
                await self.web_widget.cleanup()
        
            
            logger.info("Ventana principal limpiada")
            
        except Exception as e:
            logger.error(f"Error limpiando ventana principal: {e}")
    
    def get_widget(self, widget_name: str):
        """
        Obtiene una referencia a un widget específico.
        
        Args:
            widget_name: Nombre del widget ('chat', 'camera', 'web', 'status')
            
        Returns:
            El widget solicitado o None si no existe
        """
        widgets = {
            'chat': self.chat_widget,
            'camera': self.camera_widget,
            'web': self.web_widget
        }
        
        return widgets.get(widget_name)
    
    def update_layout(self):
        """Actualiza el layout de la ventana."""
        self._configure_splitter_sizes()
        self.update()
        
        logger.debug("Layout actualizado")
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas de la ventana principal.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'widgets_initialized': {
                'chat': self.chat_widget is not None,
                'camera': self.camera_widget is not None,
                'web': self.web_widget is not None
            }
        }
        
        # Agregar estadísticas de widgets si están inicializados
        if self.chat_widget:
            stats['chat_stats'] = self.chat_widget.get_stats()
        
        if self.camera_widget:
            stats['camera_stats'] = self.camera_widget.get_stats()
        
        if self.web_widget:
            stats['web_stats'] = self.web_widget.get_stats()
        
        return stats