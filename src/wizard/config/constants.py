"""
Constantes de la aplicación SHARA Wizard
"""

from enum import Enum

# Estados emocionales del robot
class RobotState(Enum):
    """Estados emocionales disponibles para el robot."""
    ATTENTION = "surprise"
    HELLO = "neutral"
    NO = "no"
    YES = "silly"
    ANGRY = "angry"
    SAD = "sad"
    JOY = "joy"
    BLUSH = "joy_blush"

# Tipos de mensaje
class MessageType(Enum):
    """Tipos de mensaje en el sistema."""
    CLIENT = "client_message"
    ROBOT = "robot_message"
    WIZARD = "wizard_message"
    OPENAI = "openai_message"
    TRANSCRIPTION = "transcription_result"
    USER_DETECTED = "user_detected"
    USER_LOST = "user_lost"

# Estados de conexión
class ConnectionState(Enum):
    """Estados de conexión de los servicios."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    REGISTERED = "registered"
    ERROR = "error"

# Modos de operación
class OperationMode(Enum):
    """Modos de operación del wizard."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"

# Eventos del sistema
class SystemEvent(Enum):
    """Eventos del sistema para el gestor de eventos."""
    # Eventos de conexión
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    REGISTRATION_SUCCESS = "registration_success"
    
    # Eventos de mensaje
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    
    # Eventos de usuario
    USER_DETECTED = "user_detected"
    USER_LOST = "user_lost"
    USER_IDENTIFIED = "user_identified"
    
    # Eventos de video
    VIDEO_FRAME_RECEIVED = "video_frame_received"
    VIDEO_CONNECTION_STATUS = "video_connection_status"
    
    # Eventos de modo
    MODE_CHANGED = "mode_changed"
    
    # Eventos de aplicación
    APP_INITIALIZED = "app_initialized"
    APP_CLOSING = "app_closing"

# Configuraciones de interfaz
WINDOW_GEOMETRY = {
    'DEFAULT_WIDTH': 1400,
    'DEFAULT_HEIGHT': 900,
    'MIN_WIDTH': 800,
    'MIN_HEIGHT': 600
}

SPLITTER_RATIOS = {
    'MAIN_HORIZONTAL': [40, 60],  # Chat: 40%, Derecha: 60%
    'RIGHT_VERTICAL': [40, 60]    # Cámara: 40%, Web: 60%
}

# Configuraciones de video
VIDEO_CONFIG = {
    'FRAME_WIDTH': 320,
    'FRAME_HEIGHT': 240,
    'MAX_FRAMES_RECEIVED': 1000,
    'RECONNECT_DELAY': 5,
    'MAX_RECONNECT_ATTEMPTS': 10
}

# Configuraciones de chat
CHAT_CONFIG = {
    'MAX_MESSAGES': 100,
    'AUTO_SCROLL': True,
    'KEEPALIVE_INTERVAL': 30  # segundos
}

# Configuraciones de timeout
TIMEOUTS = {
    'SOCKET_CONNECT': 10,
    'SOCKET_RESPONSE': 30,
    'KEEPALIVE': 30,
    'RECONNECT_DELAY': 5,
    'USER_RESPONSE': 300  # 5 minutos para respuesta del usuario
}

# Configuraciones de estilo
STYLE_COLORS = {
    'PRIMARY': '#2c3e50',
    'SECONDARY': '#34495e',
    'SUCCESS': '#27ae60',
    'WARNING': '#f39c12',
    'ERROR': '#e74c3c',
    'INFO': '#3498db',
    'BACKGROUND': '#f8f9fa',
    'BORDER': '#dcdcdc'
}