"""
Servicio de mensajería para SHARA Wizard
"""

import asyncio
import json
from typing import Optional, List, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from config import RobotState, MessageType, OperationMode
from core.event_manager import EventManager
from services.socket_service import SocketService
from models import Message, MessageSender, Session, User
from utils.logger import get_logger

logger = get_logger(__name__)

class MessageService(QObject):
    """
    Servicio que maneja toda la lógica de mensajería, incluyendo
    procesamiento de mensajes, gestión de sesiones y comunicación.
    """
    
    # Señales Qt
    message_processed = pyqtSignal(Message)
    message_sent = pyqtSignal(Message)
    session_started = pyqtSignal(str)  # session_id
    session_ended = pyqtSignal(str)    # session_id
    user_response_required = pyqtSignal(Message, str)  # message, state
    user_response_with_states_required = pyqtSignal(object, dict, str)
    
    def __init__(self, event_manager: EventManager, socket_service: SocketService):
        super().__init__()
        
        self.event_manager = event_manager
        self.socket_service = socket_service
        
        # Estado del servicio
        self.current_session: Optional[Session] = None
        self.current_user: Optional[User] = None
        self.operation_mode = OperationMode.MANUAL
        self.auto_mode_enabled = False
        
        # Cola de mensajes pendientes
        self.pending_messages: List[Message] = []
        self.is_processing = False
        
        # Timer para keep-alive
        self.keepalive_timer = QTimer()
        self.keepalive_timer.timeout.connect(self._send_keepalive)
        
        # Callbacks personalizados
        self._message_callbacks: Dict[str, List[Callable]] = {}
        
        self._setup_event_subscriptions()
        self.__pending_tasks = []
        logger.debug("MessageService inicializado")
    
    async def initialize(self):
        """Inicializa el servicio de mensajería."""
        try:
            logger.info("Inicializando servicio de mensajería...")
            
            # Configurar callbacks de socket
            self.socket_service.add_event_callback('client_message_for_wizard', self._handle_client_message)
            self.socket_service.add_event_callback('openai_message', self._handle_openai_message)
            self.socket_service.add_event_callback('openai_message_with_states', self._handle_openai_message_with_states)
            self.socket_service.add_event_callback('wizard_message', self._handle_wizard_message)
            self.socket_service.add_event_callback('user_detected', self._handle_user_detected)
            self.socket_service.add_event_callback('user_lost', self._handle_user_lost)
            self.socket_service.add_event_callback('voice_response_confirmation', self._handle_wizard_message)
            
            # Iniciar timer de keep-alive
            self.keepalive_timer.start(30000)  # 30 segundos
            
            logger.info("Servicio de mensajería inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando servicio de mensajería: {e}")
            raise
    
    async def cleanup(self):
        """Limpia recursos del servicio."""
        try:
            for task in self.__pending_tasks:
                if not task.done():
                    task.cancel()

            try:
                await asyncio.gather(*self.__pending_tasks, return_exceptions=True)
            except Exception:
                pass

            self.__pending_tasks.clear()
            
            logger.info("Limpiando servicio de mensajería...")
            
            # Detener timer
            self.keepalive_timer.stop()
            
            # Finalizar sesión actual
            if self.current_session and self.current_session.is_active():
                self.current_session.end()
            
            # Limpiar callbacks
            self._message_callbacks.clear()
            
            logger.info("Servicio de mensajería limpiado")
            
        except Exception as e:
            logger.error(f"Error limpiando servicio de mensajería: {e}")
    
    def _setup_event_subscriptions(self):
        """Configura suscripciones a eventos del sistema."""
        self.event_manager.subscribe('mode_changed', self._handle_mode_changed)
        self.event_manager.subscribe('user_identified', self._handle_user_identified)
    
    def _handle_mode_changed(self, new_mode: OperationMode):
        """Maneja cambio de modo de operación."""
        self.operation_mode = new_mode
        self.auto_mode_enabled = (new_mode == OperationMode.AUTOMATIC)
        
        logger.info(f"Modo de operación cambiado a: {new_mode.value}")
        
    
    def _handle_user_identified(self, user: User):
        """Maneja cuando un usuario es identificado."""
        if self.current_user and self.current_user.user_id == user.user_id:
            self.current_user = user
            
            if self.current_session:
                self.current_session.set_user(user)
            
            logger.info(f"Usuario actual actualizado: {user.get_display_name()}")
    
    def _handle_client_message(self, data: Dict[str, Any]):
        """Maneja mensajes del cliente."""
        try:
            message = Message.create_client_message(
                text=data.get('text', ''),
                user_id=self.current_user.user_id if self.current_user else None,
                session_id=self.current_session.session_id if self.current_session else None
            )
            
            self._add_message_to_session(message)
            self.event_manager.emit('message_received', message, source='message_service')
            
            # Marcar que requiere respuesta
            message.requires_response = True
            self.pending_messages.append(message)
            
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de cliente: {e}")
    
    def _handle_openai_message(self, data: Dict[str, Any]):
        """Maneja mensajes de OpenAI (robot)."""
        try:
            # Crear mensaje del robot
            robot_state = None
            if data.get('state'):
                try:
                    robot_state = RobotState(data['state'])
                except ValueError:
                    robot_state = RobotState.ATTENTION
            
            message = Message.create_robot_message(
                text=data.get('text', ''),
                robot_state=robot_state,
                user_id=self.current_user.user_id if self.current_user else None,
                session_id=self.current_session.session_id if self.current_session else None
            )
            
            # En modo manual, mostrar diálogo de respuesta
            if not self.auto_mode_enabled:
                state_value = robot_state.value if robot_state else 'attention'
                self.user_response_required.emit(message, state_value)
            else:
                # En modo automático, NO añadir a sesión, solo enviar directamente
                # El robot_message que venga de vuelta será el que se muestre
                logger.debug("Enviando respuesta automática sin mostrar en chat (evitar duplicidad)")
                asyncio.create_task(self._send_automatic_wizard_response(message))
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de OpenAI: {e}")

    def _handle_openai_message_with_states(self, data: Dict[str, Any]):
        """Maneja mensajes de OpenAI con respuestas por estado emocional (solo en modo manual)."""
        try:
            main_response = data.get('main_response', {})
            state_responses = data.get('state_responses', {})
            user_message = data.get('user_message', '')

            if not isinstance(state_responses, dict):
                logger.warning(f"state_responses no es un diccionario: {type(state_responses)}, usando diccionario vacío")
                state_responses = {}

            robot_state = None
            if main_response.get('state'):
                try:
                    robot_state = RobotState(main_response['state'])
                except ValueError:
                    robot_state = RobotState.ATTENTION

            message = Message.create_robot_message(
                text=main_response.get('text', ''),
                robot_state=robot_state,
                user_id=self.current_user.user_id if self.current_user else None,
                session_id=self.current_session.session_id if self.current_session else None
            )

            self._add_message_to_session(message)

            # En modo manual, eofrecer las opciones de respuesta por estado
            if not self.auto_mode_enabled:
                self.user_response_with_states_required.emit(message, state_responses, user_message)

        except Exception as e:
            logger.error(f"Error procesando mensaje de OpenAI con estados: {e}")
            fallback_data = {
                'text': data.get('main_response', {}).get('text', ''),
                'state': data.get('main_response', {}).get('state', 'attention')
            }
            self._handle_openai_message(fallback_data)
    
    def _handle_wizard_message(self, data: Dict[str, Any]):
        """Maneja mensajes del wizard/operador."""
        try:
            robot_state = None
            if data.get('state'):
                try:
                    robot_state = RobotState(data['state'])
                except ValueError:
                    robot_state = RobotState.ATTENTION
            
            message = Message.create_wizard_message(
                text=data.get('text', ''),
                robot_state=robot_state,
                user_id=self.current_user.user_id if self.current_user else None,
                session_id=self.current_session.session_id if self.current_session else None
            )
            
            self._add_message_to_session(message)
            self.event_manager.emit('wizard_message_received', message, source='message_service')
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de wizard: {e}")
    
    def _handle_user_detected(self, data: Dict[str, Any]):
        """Maneja detección de usuario."""
        try:
            # Crear o actualizar usuario
            user = User(
                user_id=data.get('userId', 'unknown'),
                user_name=data.get('userName'),
                is_new_user=data.get('isNewUser', False),
                needs_identification=data.get('needsIdentification', True),
                confidence=data.get('consensusRatio', 0.0)
            )
            
            # Si cambió de usuario, finalizar sesión anterior
            if (self.current_user and 
                self.current_user.user_id != user.user_id and 
                self.current_session and 
                self.current_session.is_active()):
                
                self.current_session.end()
                self.session_ended.emit(self.current_session.session_id)
            
            # Establecer usuario actual y crear nueva sesión
            self.current_user = user
            self._start_new_session()
            
            logger.info(f"Usuario detectado: {user.get_display_name()}")
            
        except Exception as e:
            logger.error(f"Error procesando detección de usuario: {e}")
    
    def _handle_user_lost(self, data: Dict[str, Any]):
        """Maneja pérdida de usuario."""
        try:
            user_id = data.get('userId')
            
            if (self.current_user and 
                self.current_user.user_id == user_id and 
                self.current_session and 
                self.current_session.is_active()):
                
                self.current_session.end()
                self.session_ended.emit(self.current_session.session_id)
                
                logger.info(f"Usuario perdido: {self.current_user.get_display_name()}")
                
                # Limpiar usuario actual después de un delay
                asyncio.create_task(self._clear_current_user_delayed())
            
        except Exception as e:
            logger.error(f"Error procesando pérdida de usuario: {e}")
            
    async def _clear_current_user_delayed(self, delay: int = 5):
        """Limpia el usuario actual después de un delay."""
        await asyncio.sleep(delay)
        self.current_user = None
        self.current_session = None
    
    def _start_new_session(self):
        """Inicia una nueva sesión."""
        self.current_session = Session()
        
        if self.current_user:
            self.current_session.set_user(self.current_user)
        
        self.current_session.start()
        self.session_started.emit(self.current_session.session_id)
        
        logger.info(f"Nueva sesión iniciada: {self.current_session.session_id}")
    
    def _add_message_to_session(self, message: Message):
        """Agrega un mensaje a la sesión actual."""
        if not self.current_session:
            self._start_new_session()
        
        success = self.current_session.add_message(message)
        if success:
            message.mark_processed()
            self.message_processed.emit(message)
    
    def _get_preset_response(self) -> str:
        """Obtiene una respuesta predefinida."""
        # Por ahora retornar una respuesta genérica
        # En el futuro esto se reemplazará con llamadas a OpenAI
        return "Entiendo lo que dices. ¿Puedes contarme más al respecto?"
    
    async def send_wizard_message(self, text: str, state: RobotState = RobotState.ATTENTION) -> bool:
        """
        Envía un mensaje del wizard.
        
        Args:
            text: Texto del mensaje
            state: Estado emocional del robot
            
        Returns:
            True si fue enviado correctamente
        """
        try:
            # Crear mensaje
            message = Message.create_wizard_message(
                text=text,
                robot_state=state,
                user_id=self.current_user.user_id if self.current_user else None,
                session_id=self.current_session.session_id if self.current_session else None
            )
            
            # Agregar a sesión
            self._add_message_to_session(message)
            
            # Enviar por socket
            success = await self.socket_service.send_wizard_message(text, state.value)
            
            if success:
                message.mark_sent()
                self.message_sent.emit(message)
                logger.debug(f"Mensaje del wizard enviado: {text[:50]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"Error enviando mensaje del wizard: {e}")
            return False

    async def _send_automatic_wizard_response(self, openai_message: Message):
        """
        Envía automáticamente un mensaje de OpenAI como respuesta del wizard.
        
        Args:
            openai_message: Mensaje recibido de OpenAI que se enviará como wizard
        """
        try:
            # Usar el mismo método que en modo manual, pero automáticamente
            success = await self.send_wizard_message(
                openai_message.text, 
                openai_message.robot_state or RobotState.ATTENTION
            )
            
            if success:
                logger.info(f"Respuesta automática enviada como wizard: {openai_message.text[:50]}...")
            else:
                logger.error("Error enviando respuesta automática del wizard")
                
        except Exception as e:
            logger.error(f"Error de exception enviando respuesta automática del wizard: {e}")
    
    def _send_keepalive(self):
        """Envía señal de keep-alive."""
        if self.socket_service.is_connected:
            asyncio.create_task(self.socket_service.send_message('ping', {}))
    
    def set_operation_mode(self, mode: OperationMode):
        """
        Establece el modo de operación.
        
        Args:
            mode: Nuevo modo de operación
        """
        if self.operation_mode != mode:
            old_mode = self.operation_mode
            self.operation_mode = mode
            self.auto_mode_enabled = (mode == OperationMode.AUTOMATIC)
            
            self.event_manager.emit('mode_changed', mode, source='message_service')
            logger.info(f"Modo cambiado de {old_mode.value} a {mode.value}")
    
    def get_current_session_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Obtiene mensajes de la sesión actual.
        
        Args:
            limit: Límite de mensajes a devolver
            
        Returns:
            Lista de mensajes
        """
        if not self.current_session:
            return []
        
        return self.current_session.get_messages(limit=limit)
    
    def add_message_callback(self, message_type: str, callback: Callable):
        """
        Agrega un callback para un tipo de mensaje específico.
        
        Args:
            message_type: Tipo de mensaje
            callback: Función callback
        """
        if message_type not in self._message_callbacks:
            self._message_callbacks[message_type] = []
        
        self._message_callbacks[message_type].append(callback)
        logger.debug(f"Callback agregado para {message_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'operation_mode': self.operation_mode.value,
            'auto_mode_enabled': self.auto_mode_enabled,
            'current_session_id': self.current_session.session_id if self.current_session else None,
            'current_user_id': self.current_user.user_id if self.current_user else None,
            'pending_messages': len(self.pending_messages),
            'is_processing': self.is_processing,
            'session_message_count': len(self.current_session.messages) if self.current_session else 0
        }