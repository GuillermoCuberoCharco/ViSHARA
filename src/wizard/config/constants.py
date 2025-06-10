"""
Constantes de la aplicación SHARA Wizard
"""

from enum import Enum

# Estados emocionales del robot
class RobotState(Enum):
    """Estados emocionales disponibles para el robot."""
    ATTENTION = "Attention"
    HELLO = "Hello"
    NO = "No"
    YES = "Yes"
    ANGRY = "Angry"
    SAD = "Sad"
    JOY = "Joy"
    BLUSH = "Blush"

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

# Respuestas predefinidas por estado
PRESET_RESPONSES = {
    RobotState.ATTENTION: [
        "Estoy prestando atención a lo que dices.",
        "Me interesa mucho este tema.",
        "Continúa, te escucho atentamente.",
        "Entiendo tu punto de vista."
    ],
    RobotState.HELLO: [
        "¡Hola! ¿Cómo estás hoy?",
        "¡Qué gusto verte de nuevo!",
        "¡Bienvenido/a!",
        "¡Hola! Espero que estés teniendo un buen día."
    ],
    RobotState.NO: [
        "Lo siento, pero no puedo hacer eso.",
        "Me temo que eso no es posible.",
        "Desafortunadamente, no es viable.",
        "No, pero podríamos buscar una alternativa."
    ],
    RobotState.YES: [
        "¡Sí, por supuesto!",
        "Me parece una excelente idea.",
        "Estoy de acuerdo contigo.",
        "Definitivamente podemos hacer eso."
    ],
    RobotState.ANGRY: [
        "Entiendo tu frustración.",
        "Comprendo que esto puede ser molesto.",
        "Vamos a resolver esto juntos.",
        "Tu molestia es válida, busquemos una solución."
    ],
    RobotState.SAD: [
        "Lamento que te sientas así.",
        "Estoy aquí para escucharte.",
        "Comprendo que es una situación difícil.",
        "¿Cómo puedo ayudarte a sentirte mejor?"
    ],
    RobotState.JOY: [
        "¡Me alegro mucho por ti!",
        "¡Esas son excelentes noticias!",
        "¡Qué maravilloso momento!",
        "¡Comparto tu felicidad!"
    ],
    RobotState.BLUSH: [
        "Me siento halagado/a.",
        "Gracias por tus amables palabras.",
        "Eres muy amable al decir eso.",
        "Me alegra que valores mi ayuda."
    ]
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