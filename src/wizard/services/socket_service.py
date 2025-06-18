"""
Servicio de WebSocket para SHARA Wizard
"""

import base64
import asyncio
import json
from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal
import socketio

from config import settings, ConnectionState, MessageType
from core.event_manager import EventManager
from utils.logger import get_logger

logger = get_logger(__name__)

class SocketService(QObject):
    """
    Servicio que maneja todas las conexiones WebSocket con el servidor Node.
    """
    
    # Señales Qt
    connection_established = pyqtSignal()
    connection_lost = pyqtSignal()
    connection_error = pyqtSignal(str)
    message_received = pyqtSignal(str, object)
    registration_success = pyqtSignal()
    
    def __init__(self, event_manager: EventManager):
        super().__init__()
        
        self.event_manager = event_manager
        self.sio = None
        self.state = ConnectionState.DISCONNECTED
        self.is_registered = False
        self.connection_retries = 0
        self.max_retries = settings.server.reconnect_attempts
        
        # Configuración de conexión
        self.server_url = settings.server.url
        self.message_path = settings.sockets.message_path
        self.video_path = settings.sockets.video_path
        self.transports = settings.sockets.transports
        
        # Callbacks para eventos específicos
        self._event_callbacks: Dict[str, list] = {}
        
        logger.debug("SocketService inicializado")
    
    async def initialize(self):
        """Inicializa el servicio de socket."""
        try:
            logger.info("Inicializando servicio de socket...")
            await self._setup_socket_client()
            await self.connect()
            logger.info("Servicio de socket inicializado")
        except Exception as e:
            logger.error(f"Error inicializando servicio de socket: {e}")
            raise
    
    async def cleanup(self):
        """Limpia recursos del servicio."""
        try:
            logger.info("Limpiando servicio de socket...")
            await self.disconnect()
            self._event_callbacks.clear()
            logger.info("Servicio de socket limpiado")
        except Exception as e:
            logger.error(f"Error limpiando servicio de socket: {e}")
    
    async def _setup_socket_client(self):
        """Configura el cliente de socket."""
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=self.max_retries,
            reconnection_delay=settings.server.reconnect_delay,
            logger=False,
            engineio_logger=False,
        )
        self._setup_event_handlers()
        
        logger.debug("Cliente de socket configurado")
    
    def _setup_event_handlers(self):
        """Configura los manejadores de eventos del socket."""
        
        @self.sio.event
        async def connect():
            logger.info('Conexión Socket.IO establecida')
            self.state = ConnectionState.CONNECTED
            self.connection_retries = 0
            self.connection_established.emit()
            self.event_manager.emit('connection_established', source='socket_service')
            
            # Registrar cliente automáticamente
            try:
                await self.sio.emit('register_operator', 'python')
                logger.info('Cliente Python registrado')
            except Exception as e:
                logger.error(f'Error registrando cliente Python: {e}')
        
        @self.sio.event
        async def registration_confirmed(data):
            logger.info('Registro confirmado por el servidor: {data}')
            self.is_registered = True
            self.registration_success.emit()
            self.event_manager.emit('registration_success', source='socket_service')
        
        @self.sio.event
        async def connect_error(error):
            logger.error(f'Error de conexión Socket.IO: {error}')
            self.state = ConnectionState.ERROR
            self.connection_error.emit(str(error))
            self.event_manager.emit('connection_error', str(error), source='socket_service')
        
        @self.sio.event
        async def disconnect():
            logger.info('Desconectado del servidor')
            self.state = ConnectionState.DISCONNECTED
            self.is_registered = False
            self.connection_lost.emit()
            self.event_manager.emit('connection_lost', source='socket_service')
        
        # Manejadores de mensajes
        @self.sio.event
        async def client_message(data):
            logger.debug(f'Mensaje de cliente recibido: {data}')
            self._handle_message('client_message', data)
        
        @self.sio.event
        async def openai_message(data):
            logger.debug(f'Mensaje de OpenAI recibido: {data}')
            self._handle_message('openai_message', data)
        
        @self.sio.event
        async def openai_message_with_states(data):
            logger.debug(f'Respuestas múltiples de OpenAI por estados recibidas: {data}')
            self._handle_message('openai_message_with_states', data)

        @self.sio.event
        async def robot_message(data):
            logger.debug(f'Mensaje de robot recibido: {data}')
            self._handle_message('robot_message', data)
        
        @self.sio.event
        async def wizard_message(data):
            logger.debug(f'Mensaje de wizard recibido: {data}')
            self._handle_message('wizard_message', data)
        
        @self.sio.event
        async def user_detected(data):
            logger.debug(f'Usuario detectado: {data}')
            self._handle_message('user_detected', data)
        
        @self.sio.event
        async def user_lost(data):
            logger.debug(f'Usuario perdido: {data}')
            self._handle_message('user_lost', data)
    
    def _handle_message(self, event_type: str, data: Any):
        """
        Maneja los mensajes recibidos del servidor.
        
        Args:
            event_type: Tipo de evento recibido
            data: Datos del mensaje
        """
        try:
            # Emitir señal Qt
            self.message_received.emit(event_type, data)
            
            # Emitir evento en el event manager
            self.event_manager.emit(f'message_{event_type}', data, source='socket_service')
            
            # Llamar callbacks específicos si existen
            if event_type in self._event_callbacks:
                for callback in self._event_callbacks[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f'Error en callback para {event_type}: {e}')
            
        except Exception as e:
            logger.error(f'Error manejando mensaje {event_type}: {e}')
    
    async def connect(self) -> bool:
        """
        Conecta al servidor con reintentos.
        
        Returns:
            True si la conexión fue exitosa
        """
        while self.connection_retries < self.max_retries:
            try:
                logger.info(f'Intentando conectar al servidor: {self.server_url}')
                self.state = ConnectionState.CONNECTING
                
                await self.sio.connect(
                    self.server_url,
                    socketio_path=self.message_path,
                    transports=self.transports,
                    wait=True,
                    wait_timeout=settings.server.timeout
                )
                
                logger.info('Conectado al servidor exitosamente')
                return True
                
            except Exception as e:
                self.connection_retries += 1
                logger.error(f'Error en intento de conexión {self.connection_retries}: {e}')
                
                if self.connection_retries < self.max_retries:
                    delay = settings.server.reconnect_delay * (2 ** (self.connection_retries - 1))
                    logger.info(f'Reintentando en {delay} segundos...')
                    await asyncio.sleep(delay)
                else:
                    logger.error('Máximo número de reintentos alcanzado')
                    self.state = ConnectionState.ERROR
                    break
        
        return False
    
    async def disconnect(self):
        """Desconecta del servidor."""
        if self.sio and self.sio.connected:
            try:
                await self.sio.disconnect()
                logger.info('Desconectado del servidor')
            except Exception as e:
                logger.error(f'Error desconectando: {e}')
        
        self.state = ConnectionState.DISCONNECTED
        self.is_registered = False
    
    async def send_message(self, event: str, data: Any) -> bool:
        """
        Envía un mensaje al servidor.
        
        Args:
            event: Nombre del evento
            data: Datos a enviar
            
        Returns:
            True si el mensaje fue enviado correctamente
        """
        if not self.is_connected:
            logger.error('No hay conexión para enviar mensaje')
            return False
        
        try:
            await self.sio.emit(event, data)
            logger.debug(f'Mensaje enviado: {event}')
            return True
        except Exception as e:
            logger.error(f'Error enviando mensaje {event}: {e}')
            return False
    
    async def send_wizard_message(self, text: str, state: str = 'Attention') -> bool:
        """
        Envía un mensaje del wizard/operador.
        
        Args:
            text: Texto del mensaje
            state: Estado emocional del robot
            
        Returns:
            True si fue enviado correctamente
        """
        message_data = {
            'type': 'wizard_message',
            'text': text,
            'state': state
        }
        
        return await self.send_message('message', message_data)
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """
        Agrega un callback para un tipo de evento específico.
        
        Args:
            event_type: Tipo de evento
            callback: Función callback
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        
        self._event_callbacks[event_type].append(callback)
        logger.debug(f'Callback agregado para {event_type}')
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """
        Remueve un callback para un tipo de evento específico.
        
        Args:
            event_type: Tipo de evento
            callback: Función callback
        """
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
                logger.debug(f'Callback removido para {event_type}')
            except ValueError:
                logger.warning(f'Callback no encontrado para {event_type}')
    
    @property
    def is_connected(self) -> bool:
        """Verifica si está conectado al servidor."""
        return (
            self.sio is not None and 
            self.sio.connected and 
            self.state == ConnectionState.CONNECTED
        )
    
    @property
    def connection_state(self) -> ConnectionState:
        """Obtiene el estado actual de la conexión."""
        return self.state

    async def send_voice_response(self, audio_data: bytes, robot_state: str) -> bool:
        """
        Envía una respuesta de voz directamente al servidor.
        
        Args:
            audio_data: Datos de audio en formato bytes
            robot_state: Estado emocional del robot
            
        Returns:
            True si el mensaje fue enviado correctamente
        """
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        voice_data = {
            'audio': audio_b64,
            'format': 'wav',
            'robot_state': robot_state,
        }

        return await self.send_message('voice_response', voice_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'is_connected': self.is_connected,
            'is_registered': self.is_registered,
            'connection_state': self.state.value,
            'server_url': self.server_url,
            'connection_retries': self.connection_retries,
            'max_retries': self.max_retries,
            'registered_callbacks': {
                event: len(callbacks) 
                for event, callbacks in self._event_callbacks.items()
            }
        }