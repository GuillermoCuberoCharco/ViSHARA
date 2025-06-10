"""
Servicio de video para SHARA Wizard
"""

import asyncio
import base64
import json
from typing import Optional, Callable
import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
import socketio

from config import settings, VIDEO_CONFIG, ConnectionState
from core.event_manager import EventManager
from services.socket_service import SocketService
from utils.logger import get_logger

logger = get_logger(__name__)

class VideoService(QObject):
    """
    Servicio que maneja la recepción y procesamiento de video
    desde el servidor SHARA.
    """
    
    # Señales Qt
    frame_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(str)
    video_error = pyqtSignal(str)
    
    def __init__(self, event_manager: EventManager, socket_service: SocketService):
        super().__init__()
        
        self.event_manager = event_manager
        self.socket_service = socket_service
        
        # Cliente de video independiente
        self.video_sio = None
        self.is_video_connected = False
        self.is_subscribed = False
        
        # Estado del servicio
        self.frames_received = 0
        self.connection_attempts = 0
        self.max_connection_attempts = VIDEO_CONFIG['MAX_RECONNECT_ATTEMPTS']
        self.reconnect_delay = VIDEO_CONFIG['RECONNECT_DELAY']
        
        # Configuración
        self.server_url = settings.server.url
        self.video_path = settings.sockets.video_path
        
        # Callbacks para frames
        self._frame_callbacks: list = []
        
        logger.debug("VideoService inicializado")
    
    async def initialize(self):
        """Inicializa el servicio de video."""
        try:
            logger.info("Inicializando servicio de video...")
            await self._setup_video_client()
            await self._connect_video()
            logger.info("Servicio de video inicializado")
        except Exception as e:
            logger.error(f"Error inicializando servicio de video: {e}")
            # No propagamos el error ya que el video no es crítico
    
    async def cleanup(self):
        """Limpia recursos del servicio."""
        try:
            logger.info("Limpiando servicio de video...")
            await self._disconnect_video()
            self._frame_callbacks.clear()
            logger.info("Servicio de video limpiado")
        except Exception as e:
            logger.error(f"Error limpiando servicio de video: {e}")
    
    async def _setup_video_client(self):
        """Configura el cliente de video independiente."""
        try:
            engineio_opts = {
                'logger': False,
                'engineio_logger': False
            }
            
            self.video_sio = socketio.AsyncClient(
                reconnection=True,
                reconnection_attempts=self.max_connection_attempts,
                engineio_opts=engineio_opts
            )
            
            self._setup_video_event_handlers()
            logger.debug("Cliente de video configurado")
            
        except Exception as e:
            logger.error(f"Error configurando cliente de video: {e}")
            raise
    
    def _setup_video_event_handlers(self):
        """Configura los manejadores de eventos del cliente de video."""
        
        @self.video_sio.event
        async def connect():
            logger.info('Conexión de video establecida')
            self.is_video_connected = True
            self.connection_attempts = 0
            self.connection_status_changed.emit("Conectado al servidor de video")
            
            # Suscribirse automáticamente al stream de video
            try:
                await self.video_sio.emit('subscribe_video')
                logger.info('Suscrito al stream de video')
            except Exception as e:
                logger.error(f'Error suscribiéndose al video: {e}')
        
        @self.video_sio.event
        async def connect_error():
            logger.error('Error de conexión de video')
            self.is_video_connected = False
            self.connection_status_changed.emit("Error de conexión de video")
            
            # Intentar reconectar
            await self._handle_video_reconnection()
        
        @self.video_sio.event
        async def disconnect():
            logger.info('Desconectado del servidor de video')
            self.is_video_connected = False
            self.is_subscribed = False
            self.connection_status_changed.emit("Desconectado del servidor de video")
        
        @self.video_sio.event
        async def subcription_success(data):
            logger.info('Suscripción al video exitosa')
            self.is_subscribed = True
            self.connection_status_changed.emit("Suscrito al stream de video")
        
        @self.video_sio.on('video-frame')
        async def on_video_frame(data):
            await self._process_video_frame(data)
    
    async def _connect_video(self):
        """Conecta al servidor de video."""
        try:
            logger.info(f'Conectando al servidor de video: {self.server_url}')
            
            await self.video_sio.connect(
                self.server_url,
                socketio_path=self.video_path,
                transports=['websocket'],
                wait=True,
                wait_timeout=settings.server.timeout
            )
            
            logger.info('Conectado al servidor de video exitosamente')
            
        except Exception as e:
            logger.error(f'Error conectando al servidor de video: {e}')
            self.video_error.emit(f"Error de conexión: {str(e)}")
            await self._handle_video_reconnection()
    
    async def _disconnect_video(self):
        """Desconecta del servidor de video."""
        if self.video_sio and self.is_video_connected:
            try:
                # Desuscribirse del video
                if self.is_subscribed:
                    await self.video_sio.emit('unsubscribe_video')
                
                await self.video_sio.disconnect()
                logger.info('Desconectado del servidor de video')
            except Exception as e:
                logger.error(f'Error desconectando del video: {e}')
        
        self.is_video_connected = False
        self.is_subscribed = False
    
    async def _handle_video_reconnection(self):
        """Maneja la reconexión automática del video."""
        if self.connection_attempts >= self.max_connection_attempts:
            logger.error('Máximo número de intentos de reconexión de video alcanzado')
            self.connection_status_changed.emit("Max reconnect attempts reached. Stopping...")
            return
        
        self.connection_attempts += 1
        delay = min(30, self.reconnect_delay * (2 ** (self.connection_attempts - 1)))
        
        logger.info(f'Reintentando conexión de video en {delay} segundos... (intento {self.connection_attempts})')
        self.connection_status_changed.emit(f"Reconectando en {delay} segundos...")
        
        await asyncio.sleep(delay)
        
        try:
            await self._connect_video()
        except Exception as e:
            logger.error(f'Error en intento de reconexión de video: {e}')
    
    async def _process_video_frame(self, data):
        """
        Procesa un frame de video recibido.
        
        Args:
            data: Datos del frame
        """
        try:
            # Extraer datos del frame
            frame_data = None
            if isinstance(data, dict):
                frame_data = data.get('frame', '')
            else:
                frame_data = data
            
            if not frame_data:
                logger.warning("Frame de video vacío recibido")
                return
            
            # Decodificar frame base64
            if ',' in frame_data:
                frame_data = base64.b64decode(frame_data.split(',', 1)[1])
            else:
                frame_data = base64.b64decode(frame_data)
            
            # Convertir a imagen OpenCV
            frame = cv2.imdecode(
                np.frombuffer(frame_data, np.uint8), 
                cv2.IMREAD_COLOR
            )
            
            if frame is not None:
                self.frames_received += 1
                
                # Emitir señal con el frame
                self.frame_received.emit(frame)
                
                # Llamar callbacks registrados
                for callback in self._frame_callbacks:
                    try:
                        callback(frame)
                    except Exception as e:
                        logger.error(f"Error en callback de frame: {e}")
                
                # Emitir evento en el event manager
                self.event_manager.emit(
                    'video_frame_received', 
                    frame, 
                    source='video_service'
                )
                
                # Log cada 100 frames
                if self.frames_received % 100 == 0:
                    logger.debug(f"Frames recibidos: {self.frames_received}")
            else:
                logger.warning("No se pudo decodificar el frame de video")
                
        except Exception as e:
            logger.error(f"Error procesando frame de video: {e}")
            self.video_error.emit(f"Error procesando frame: {str(e)}")
    
    def add_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """
        Agrega un callback para procesar frames.
        
        Args:
            callback: Función que recibe un frame (numpy array)
        """
        if callback not in self._frame_callbacks:
            self._frame_callbacks.append(callback)
            logger.debug("Callback de frame agregado")
    
    def remove_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """
        Remueve un callback de frames.
        
        Args:
            callback: Función callback a remover
        """
        try:
            self._frame_callbacks.remove(callback)
            logger.debug("Callback de frame removido")
        except ValueError:
            logger.warning("Callback de frame no encontrado")
    
    async def subscribe_to_video(self) -> bool:
        """
        Se suscribe al stream de video.
        
        Returns:
            True si la suscripción fue exitosa
        """
        if not self.is_video_connected:
            logger.error("No hay conexión de video para suscribirse")
            return False
        
        try:
            await self.video_sio.emit('subscribe_video')
            logger.info("Suscripción al video solicitada")
            return True
        except Exception as e:
            logger.error(f"Error suscribiéndose al video: {e}")
            return False
    
    async def unsubscribe_from_video(self) -> bool:
        """
        Se desuscribe del stream de video.
        
        Returns:
            True si la desuscripción fue exitosa
        """
        if not self.is_video_connected:
            return True  # Ya está desconectado
        
        try:
            await self.video_sio.emit('unsubscribe_video')
            self.is_subscribed = False
            logger.info("Desuscripción del video solicitada")
            return True
        except Exception as e:
            logger.error(f"Error desuscribiéndose del video: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Verifica si está conectado al servidor de video."""
        return self.is_video_connected and self.video_sio and self.video_sio.connected
    
    @property
    def is_receiving_frames(self) -> bool:
        """Verifica si está recibiendo frames de video."""
        return self.is_connected and self.is_subscribed
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del servicio de video.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'is_connected': self.is_connected,
            'is_subscribed': self.is_subscribed,
            'frames_received': self.frames_received,
            'connection_attempts': self.connection_attempts,
            'max_connection_attempts': self.max_connection_attempts,
            'server_url': self.server_url,
            'video_path': self.video_path,
            'registered_callbacks': len(self._frame_callbacks)
        }
    
    def reset_stats(self):
        """Reinicia las estadísticas del servicio."""
        self.frames_received = 0
        self.connection_attempts = 0
        logger.debug("Estadísticas de video reiniciadas")