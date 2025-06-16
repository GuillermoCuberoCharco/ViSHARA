"""
Configuración general de la aplicación SHARA Wizard
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# Obtener directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

@dataclass
class ServerConfig:
    """Configuración del servidor SHARA."""
    url: str = 'https://vishara.onrender.com'
    web_url: str = 'https://vi-shara.vercel.app'
    timeout: int = 10
    reconnect_attempts: int = 10
    reconnect_delay: int = 5

@dataclass
class SocketConfig:
    """Configuración de WebSockets."""
    message_path: str = '/message-socket'
    video_path: str = '/video-socket'
    animation_path: str = '/animation-socket'
    transports: list = None
    ping_timeout: int = 60
    ping_interval: int = 25
    
    def __post_init__(self):
        if self.transports is None:
            self.transports = ['websocket', 'polling']

@dataclass
class UIConfig:
    """Configuración de la interfaz de usuario."""
    window_title: str = "SHARA Wizard of Oz Interface"
    window_width: int = 1400
    window_height: int = 900
    chat_width_ratio: float = 0.4
    camera_height_ratio: float = 0.4
    
@dataclass
class VideoConfig:
    """Configuración de video."""
    width: int = 320
    height: int = 240
    fps: int = 15
    reconnect_delay: int = 5
    max_reconnect_attempts: int = 10

@dataclass
class LoggingConfig:
    """Configuración de logging."""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

class AppSettings:
    """Configuración principal de la aplicación."""
    
    def __init__(self):
        self.server = ServerConfig()
        self.sockets = SocketConfig()
        self.ui = UIConfig()
        self.video = VideoConfig()
        self.logging = LoggingConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """Carga configuración desde variables de entorno."""
        # Configuración del servidor
        if server_url := os.getenv('SHARA_SERVER_URL'):
            self.server.url = server_url
        if web_url := os.getenv('SHARA_WEB_URL'):
            self.server.web_url = web_url
            
        # Configuración de logging
        if log_level := os.getenv('LOG_LEVEL'):
            self.logging.level = log_level.upper()
        if log_file := os.getenv('LOG_FILE'):
            self.logging.file_path = log_file
            
        # Configuración de UI
        if window_width := os.getenv('WINDOW_WIDTH'):
            try:
                self.ui.window_width = int(window_width)
            except ValueError:
                pass
        if window_height := os.getenv('WINDOW_HEIGHT'):
            try:
                self.ui.window_height = int(window_height)
            except ValueError:
                pass

# Instancia global de configuración
settings = AppSettings()

# Rutas importantes
RESOURCES_DIR = BASE_DIR / 'resources'
ICONS_DIR = RESOURCES_DIR / 'icons'
LOGS_DIR = BASE_DIR / 'logs'

# Crear directorios si no existen
RESOURCES_DIR.mkdir(exist_ok=True)
ICONS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)