"""
Servicio de gestión de estado global para SHARA Wizard
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

from config import OperationMode, ConnectionState, RobotState
from core.event_manager import EventManager
from models import User, Session
from utils.logger import get_logger

logger = get_logger(__name__)

class StateService(QObject):
    """
    Servicio que mantiene y gestiona el estado global de la aplicación.
    Actúa como una única fuente de verdad para el estado compartido.
    """
    
    # Señales Qt para cambios de estado
    operation_mode_changed = pyqtSignal(OperationMode)
    connection_state_changed = pyqtSignal(bool)
    current_user_changed = pyqtSignal(object)  # User or None
    current_session_changed = pyqtSignal(object)  # Session or None
    robot_state_changed = pyqtSignal(RobotState)
    app_status_changed = pyqtSignal(str)
    
    def __init__(self, event_manager: EventManager):
        super().__init__()
        
        self.event_manager = event_manager
        
        # Estado de operación
        self._operation_mode = OperationMode.MANUAL
        self._is_connected = False
        self._is_registered = False
        
        # Estado del usuario y sesión actual
        self._current_user: Optional[User] = None
        self._current_session: Optional[Session] = None
        
        # Estado del robot
        self._current_robot_state = RobotState.ATTENTION
        
        # Estado de la aplicación
        self._app_status = "Iniciando..."
        self._is_processing = False
        self._is_waiting_response = False
        
        # Estadísticas
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'sessions_created': 0,
            'users_detected': 0,
            'mode_changes': 0
        }
        
        # Metadatos adicionales
        self._metadata: Dict[str, Any] = {}
        
        self._setup_event_subscriptions()
        logger.debug("StateService inicializado")
    
    def _setup_event_subscriptions(self):
        """Configura suscripciones a eventos del sistema."""
        # Eventos de conexión
        self.event_manager.subscribe('connection_established', self._on_connection_established)
        self.event_manager.subscribe('connection_lost', self._on_connection_lost)
        self.event_manager.subscribe('registration_success', self._on_registration_success)
        
        # Eventos de mensajes
        self.event_manager.subscribe('message_received', self._on_message_received)
        self.event_manager.subscribe('message_sent', self._on_message_sent)
        
        # Eventos de usuario
        self.event_manager.subscribe('user_detected', self._on_user_detected)
        self.event_manager.subscribe('user_lost', self._on_user_lost)
        
        # Eventos de aplicación
        self.event_manager.subscribe('app_initialized', self._on_app_initialized)
        self.event_manager.subscribe('app_closing', self._on_app_closing)
    
    # Eventos del sistema
    def _on_connection_established(self):
        """Maneja el evento de conexión establecida."""
        self.set_connection_state(True)
        self.set_app_status("Conectado al servidor")
    
    def _on_connection_lost(self):
        """Maneja el evento de conexión perdida."""
        self.set_connection_state(False)
        self.set_app_status("Desconectado del servidor")
        self._is_registered = False
    
    def _on_registration_success(self):
        """Maneja el evento de registro exitoso."""
        self._is_registered = True
        self.set_app_status("Registrado y listo")
    
    def _on_message_received(self, message):
        """Maneja el evento de mensaje recibido."""
        self._stats['messages_received'] += 1
    
    def _on_message_sent(self, message):
        """Maneja el evento de mensaje enviado."""
        self._stats['messages_sent'] += 1
    
    def _on_user_detected(self, user_data):
        """Maneja el evento de usuario detectado."""
        self._stats['users_detected'] += 1
    
    def _on_user_lost(self, user_data):
        """Maneja el evento de usuario perdido."""
        pass
    
    def _on_app_initialized(self):
        """Maneja el evento de aplicación inicializada."""
        self.set_app_status("Aplicación inicializada")
    
    def _on_app_closing(self):
        """Maneja el evento de cierre de aplicación."""
        self.set_app_status("Cerrando aplicación...")
    
    # Métodos para gestionar el estado
    def set_operation_mode(self, mode: OperationMode):
        """
        Establece el modo de operación.
        
        Args:
            mode: Nuevo modo de operación
        """
        if self._operation_mode != mode:
            old_mode = self._operation_mode
            self._operation_mode = mode
            self._stats['mode_changes'] += 1
            
            # Emitir señales y eventos
            self.operation_mode_changed.emit(mode)
            self.event_manager.emit('mode_changed', mode, source='state_service')
            
            logger.info(f"Modo de operación cambiado: {old_mode.value} -> {mode.value}")
    
    def set_connection_state(self, connected: bool):
        """
        Establece el estado de conexión.
        
        Args:
            connected: True si está conectado
        """
        if self._is_connected != connected:
            self._is_connected = connected
            self.connection_state_changed.emit(connected)
            
            status = "Conectado" if connected else "Desconectado"
            logger.info(f"Estado de conexión cambiado: {status}")
    
    def set_current_user(self, user: Optional[User]):
        """
        Establece el usuario actual.
        
        Args:
            user: Usuario actual o None
        """
        if self._current_user != user:
            old_user = self._current_user
            self._current_user = user
            
            self.current_user_changed.emit(user)
            
            if user:
                logger.info(f"Usuario actual establecido: {user.get_display_name()}")
            else:
                logger.info("Usuario actual limpiado")
            
            # Emitir evento
            self.event_manager.emit(
                'current_user_changed', 
                {'old_user': old_user, 'new_user': user}, 
                source='state_service'
            )
    
    def set_current_session(self, session: Optional[Session]):
        """
        Establece la sesión actual.
        
        Args:
            session: Sesión actual o None
        """
        if self._current_session != session:
            old_session = self._current_session
            self._current_session = session
            
            self.current_session_changed.emit(session)
            
            if session:
                self._stats['sessions_created'] += 1
                logger.info(f"Sesión actual establecida: {session.session_id}")
            else:
                logger.info("Sesión actual limpiada")
            
            # Emitir evento
            self.event_manager.emit(
                'current_session_changed',
                {'old_session': old_session, 'new_session': session},
                source='state_service'
            )
    
    def set_robot_state(self, state: RobotState):
        """
        Establece el estado emocional del robot.
        
        Args:
            state: Nuevo estado del robot
        """
        if self._current_robot_state != state:
            old_state = self._current_robot_state
            self._current_robot_state = state
            
            self.robot_state_changed.emit(state)
            
            logger.debug(f"Estado del robot cambiado: {old_state.value} -> {state.value}")
            
            # Emitir evento
            self.event_manager.emit(
                'robot_state_changed',
                {'old_state': old_state, 'new_state': state},
                source='state_service'
            )
    
    def set_app_status(self, status: str):
        """
        Establece el estado de la aplicación.
        
        Args:
            status: Nuevo estado de la aplicación
        """
        if self._app_status != status:
            self._app_status = status
            self.app_status_changed.emit(status)
            logger.debug(f"Estado de aplicación: {status}")
    
    def set_processing_state(self, is_processing: bool):
        """
        Establece si la aplicación está procesando.
        
        Args:
            is_processing: True si está procesando
        """
        self._is_processing = is_processing
        
        if is_processing:
            self.set_app_status("Procesando...")
        elif self._is_connected:
            self.set_app_status("Listo")
    
    def set_waiting_response(self, is_waiting: bool):
        """
        Establece si la aplicación está esperando respuesta.
        
        Args:
            is_waiting: True si está esperando
        """
        self._is_waiting_response = is_waiting
        
        if is_waiting:
            self.set_app_status("Esperando respuesta...")
        elif self._is_connected:
            self.set_app_status("Listo")
    
    def add_metadata(self, key: str, value: Any):
        """
        Agrega metadatos al estado.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato del estado.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto
            
        Returns:
            Valor del metadato o default
        """
        return self._metadata.get(key, default)
    
    def increment_stat(self, stat_name: str, increment: int = 1):
        """
        Incrementa una estadística.
        
        Args:
            stat_name: Nombre de la estadística
            increment: Cantidad a incrementar
        """
        if stat_name in self._stats:
            self._stats[stat_name] += increment
        else:
            self._stats[stat_name] = increment
    
    # Propiedades de solo lectura
    @property
    def operation_mode(self) -> OperationMode:
        """Obtiene el modo de operación actual."""
        return self._operation_mode
    
    @property
    def is_connected(self) -> bool:
        """Verifica si está conectado."""
        return self._is_connected
    
    @property
    def is_registered(self) -> bool:
        """Verifica si está registrado."""
        return self._is_registered
    
    @property
    def current_user(self) -> Optional[User]:
        """Obtiene el usuario actual."""
        return self._current_user
    
    @property
    def current_session(self) -> Optional[Session]:
        """Obtiene la sesión actual."""
        return self._current_session
    
    @property
    def current_robot_state(self) -> RobotState:
        """Obtiene el estado actual del robot."""
        return self._current_robot_state
    
    @property
    def app_status(self) -> str:
        """Obtiene el estado actual de la aplicación."""
        return self._app_status
    
    @property
    def is_processing(self) -> bool:
        """Verifica si está procesando."""
        return self._is_processing
    
    @property
    def is_waiting_response(self) -> bool:
        """Verifica si está esperando respuesta."""
        return self._is_waiting_response
    
    @property
    def is_ready(self) -> bool:
        """Verifica si la aplicación está lista."""
        return (
            self._is_connected and 
            self._is_registered and 
            not self._is_processing
        )
    
    @property
    def is_manual_mode(self) -> bool:
        """Verifica si está en modo manual."""
        return self._operation_mode == OperationMode.MANUAL
    
    @property
    def is_automatic_mode(self) -> bool:
        """Verifica si está en modo automático."""
        return self._operation_mode == OperationMode.AUTOMATIC
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene todas las estadísticas.
        
        Returns:
            Diccionario con estadísticas
        """
        return self._stats.copy()
    
    def get_full_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo de la aplicación.
        
        Returns:
            Diccionario con todo el estado
        """
        return {
            'operation_mode': self._operation_mode.value,
            'is_connected': self._is_connected,
            'is_registered': self._is_registered,
            'current_user': self._current_user.to_dict() if self._current_user else None,
            'current_session': self._current_session.to_dict() if self._current_session else None,
            'current_robot_state': self._current_robot_state.value,
            'app_status': self._app_status,
            'is_processing': self._is_processing,
            'is_waiting_response': self._is_waiting_response,
            'is_ready': self.is_ready,
            'stats': self._stats,
            'metadata': self._metadata
        }
    
    def reset_stats(self):
        """Reinicia todas las estadísticas."""
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'sessions_created': 0,
            'users_detected': 0,
            'mode_changes': 0
        }
        logger.info("Estadísticas reiniciadas")
    
    def reset_state(self):
        """Reinicia el estado a valores por defecto."""
        self._operation_mode = OperationMode.MANUAL
        self._is_connected = False
        self._is_registered = False
        self._current_user = None
        self._current_session = None
        self._current_robot_state = RobotState.ATTENTION
        self._app_status = "Iniciando..."
        self._is_processing = False
        self._is_waiting_response = False
        self._metadata.clear()
        
        logger.info("Estado reiniciado")