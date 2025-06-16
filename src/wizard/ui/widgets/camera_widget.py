"""
Widget de cámara para SHARA Wizard
"""

import numpy as np
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                            QSizePolicy, QHBoxLayout)
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import pyqtSlot, Qt

from config import VIDEO_CONFIG
from services import VideoService, StateService
from utils.logger import get_logger

logger = get_logger(__name__)

class VideoFrame(QFrame):
    """Frame contenedor para el video."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Estilos del frame
        self.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 8px;
            }
        """)
        
        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Label para mostrar el video
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: none; color: white;")
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        
        # Texto por defecto
        self.video_label.setText("Esperando video...")
        self.video_label.setFont(QFont("Arial", 14))
        
        self.layout.addWidget(self.video_label)

class StatusDisplay(QWidget):
    """Display de estado de la conexión de video."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label de estado
        self.status_label = QLabel("Connecting to server...")
        self.status_label.setStyleSheet(
            "color: #e74c3c; background-color: rgba(0,0,0,0.5); "
            "padding: 4px 8px; border-radius: 4px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Label de estadísticas
        self.stats_label = QLabel("Frames: 0")
        self.stats_label.setStyleSheet(
            "color: #3498db; background-color: rgba(0,0,0,0.5); "
            "padding: 4px 8px; border-radius: 4px;"
        )
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
    
    def update_status(self, status: str, is_connected: bool = False):
        """
        Actualiza el estado mostrado.
        
        Args:
            status: Texto del estado
            is_connected: Si está conectado
        """
        self.status_label.setText(status)
        
        if is_connected:
            self.status_label.setStyleSheet(
                "color: #2ecc71; background-color: rgba(0,0,0,0.5); "
                "padding: 4px 8px; border-radius: 4px;"
            )
        else:
            self.status_label.setStyleSheet(
                "color: #e74c3c; background-color: rgba(0,0,0,0.5); "
                "padding: 4px 8px; border-radius: 4px;"
            )
    
    def update_stats(self, frames_received: int):
        """
        Actualiza las estadísticas mostradas.
        
        Args:
            frames_received: Número de frames recibidos
        """
        self.stats_label.setText(f"Frames: {frames_received}")

class CameraWidget(QWidget):
    """
    Widget que muestra el feed de video de la cámara del usuario.
    """
    
    def __init__(self, video_service: VideoService, state_service: StateService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.video_service = video_service
        self.state_service = state_service
        
        # Estado del widget
        self.frames_received = 0
        self.is_connected = False
        self.last_frame: Optional[np.ndarray] = None
        
        # Componentes UI
        self.video_frame = None
        self.status_display = None
        
        self._setup_ui()
        self._connect_signals()
        
        logger.debug("CameraWidget inicializado")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Frame de video
        self.video_frame = VideoFrame()
        layout.addWidget(self.video_frame, stretch=1)
        
        # Display de estado
        self.status_display = StatusDisplay()
        layout.addWidget(self.status_display)
        
        logger.debug("UI de cámara configurada")
    
    def _connect_signals(self):
        """Conecta las señales del servicio de video."""
        # Conectar señales del servicio de video
        self.video_service.frame_received.connect(self.display_frame)
        self.video_service.connection_status_changed.connect(self.update_status)
        self.video_service.video_error.connect(self._on_video_error)
        
        logger.debug("Señales de cámara conectadas")
    
    @pyqtSlot(np.ndarray)
    def display_frame(self, frame: np.ndarray):
        """
        Muestra un frame de video.
        
        Args:
            frame: Frame de video como array numpy
        """
        try:
            # Validar frame
            if frame is None or frame.size == 0:
                logger.warning("Frame inválido recibido")
                return
            
            # Incrementar contador
            self.frames_received += 1
            self.last_frame = frame.copy()
            
            # Convertir de BGR (OpenCV) a RGB (Qt)
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame
            
            # Crear QImage
            height, width = rgb_frame.shape[:2]
            bytes_per_line = 3 * width
            
            q_img = QImage(
                rgb_frame.data, 
                width, 
                height, 
                bytes_per_line, 
                QImage.Format.Format_RGB888
            )
            
            # Crear pixmap y escalar
            pixmap = QPixmap.fromImage(q_img)
            label_size = self.video_frame.video_label.size()
            
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Mostrar en el label
            self.video_frame.video_label.setPixmap(scaled_pixmap)
            
            # Actualizar estadísticas cada 10 frames
            if self.frames_received % 10 == 0:
                self.status_display.update_stats(self.frames_received)
            
        except Exception as e:
            logger.error(f"Error mostrando frame: {e}")
            self._show_error_message(f"Error displaying frame: {str(e)}")
    
    @pyqtSlot(str)
    def update_status(self, status: str):
        """
        Actualiza el estado de conexión mostrado.
        
        Args:
            status: Mensaje de estado
        """
        # Determinar si está conectado basado en el mensaje
        is_connected = "Connect" in status or "Subscr" in status
        self.is_connected = is_connected
        
        # Actualizar display
        self.status_display.update_status(status, is_connected)
        
        # Si se desconecta, mostrar mensaje en video
        if not is_connected:
            self._show_status_message(status)
        
        logger.debug(f"Estado de cámara: {status}")
    
    def _on_video_error(self, error: str):
        """
        Maneja errores de video.
        
        Args:
            error: Mensaje de error
        """
        logger.error(f"Error de video: {error}")
        self._show_error_message(error)
    
    def _show_status_message(self, message: str):
        """
        Muestra un mensaje de estado en el área de video.
        
        Args:
            message: Mensaje a mostrar
        """
        self.video_frame.video_label.clear()
        self.video_frame.video_label.setText(message)
        self.video_frame.video_label.setStyleSheet(
            "border: none; color: #3498db; font-size: 12px;"
        )
    
    def _show_error_message(self, message: str):
        """
        Muestra un mensaje de error en el área de video.
        
        Args:
            message: Mensaje de error
        """
        self.video_frame.video_label.clear()
        self.video_frame.video_label.setText(f"Error: {message}")
        self.video_frame.video_label.setStyleSheet(
            "border: none; color: #e74c3c; font-size: 12px;"
        )
    
    def reset_display(self):
        """Reinicia el display a estado inicial."""
        self.video_frame.video_label.clear()
        self.video_frame.video_label.setText("Esperando video...")
        self.video_frame.video_label.setStyleSheet(
            "border: none; color: white; font-size: 14px;"
        )
        
        self.frames_received = 0
        self.last_frame = None
        self.status_display.update_stats(0)
        
        logger.debug("Display de cámara reiniciado")
    
    def save_current_frame(self, filepath: str) -> bool:
        """
        Guarda el frame actual en un archivo.
        
        Args:
            filepath: Ruta del archivo donde guardar
            
        Returns:
            True si se guardó correctamente
        """
        if self.last_frame is None:
            logger.warning("No hay frame para guardar")
            return False
        
        try:
            import cv2
            success = cv2.imwrite(filepath, self.last_frame)
            
            if success:
                logger.info(f"Frame guardado en: {filepath}")
            else:
                logger.error(f"Error guardando frame en: {filepath}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error guardando frame: {e}")
            return False
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Obtiene el frame actual.
        
        Returns:
            Frame actual o None
        """
        return self.last_frame.copy() if self.last_frame is not None else None
    
    def set_no_video_message(self, message: str = "No hay video disponible"):
        """
        Establece un mensaje cuando no hay video.
        
        Args:
            message: Mensaje a mostrar
        """
        self._show_status_message(message)
    
    async def cleanup(self):
        """Limpia recursos del widget."""
        try:
            logger.info("Limpiando widget de cámara...")
            
            # Limpiar frame actual
            self.last_frame = None
            
            # Reiniciar display
            self.reset_display()
            
            logger.info("Widget de cámara limpiado")
            
        except Exception as e:
            logger.error(f"Error limpiando widget de cámara: {e}")
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del widget.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'frames_received': self.frames_received,
            'is_connected': self.is_connected,
            'has_current_frame': self.last_frame is not None,
            'video_service_stats': self.video_service.get_stats()
        }
    
    def toggle_video_subscription(self):
        """Alterna la suscripción al video."""
        if self.video_service.is_receiving_frames:
            asyncio.create_task(self.video_service.unsubscribe_from_video())
        else:
            asyncio.create_task(self.video_service.subscribe_to_video())
    
    # Métodos para control externo
    def start_video(self):
        """Inicia la recepción de video."""
        if not self.video_service.is_receiving_frames:
            asyncio.create_task(self.video_service.subscribe_to_video())
    
    def stop_video(self):
        """Detiene la recepción de video."""
        if self.video_service.is_receiving_frames:
            asyncio.create_task(self.video_service.unsubscribe_from_video())

# Importar cv2 aquí para evitar problemas de importación
try:
    import cv2
except ImportError:
    logger.warning("OpenCV no disponible. Algunas funciones de video pueden no funcionar.")
    cv2 = None

import asyncio