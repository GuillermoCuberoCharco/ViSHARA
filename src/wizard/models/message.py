"""
Modelo de mensaje para SHARA Wizard
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid

from config.constants import MessageType, RobotState

class MessageSender(Enum):
    """Remitentes posibles de mensajes."""
    CLIENT = "client"
    ROBOT = "robot"
    WIZARD = "wizard"
    SYSTEM = "system"

@dataclass
class Message:
    """
    Modelo que representa un mensaje en el sistema.
    """
    text: str
    sender: MessageSender
    message_type: MessageType = MessageType.CLIENT
    
    # Identificadores
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Metadatos temporales
    timestamp: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    # Estado del robot (para mensajes del robot/wizard)
    robot_state: Optional[RobotState] = None
    
    # Metadatos adicionales
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Estados de procesamiento
    is_processed: bool = False
    is_sent: bool = False
    requires_response: bool = False
    
    def __post_init__(self):
        """Inicialización post-creación."""
        # Validar texto
        if not self.text or not self.text.strip():
            raise ValueError("El texto del mensaje no puede estar vacío")
        
        # Limpiar texto
        self.text = self.text.strip()
        
        # Configurar tipo por defecto basado en remitente
        if self.message_type == MessageType.CLIENT and self.sender != MessageSender.CLIENT:
            self._set_default_message_type()
    
    def _set_default_message_type(self):
        """Establece el tipo de mensaje por defecto basado en el remitente."""
        type_mapping = {
            MessageSender.CLIENT: MessageType.CLIENT,
            MessageSender.ROBOT: MessageType.ROBOT,
            MessageSender.WIZARD: MessageType.WIZARD,
            MessageSender.SYSTEM: MessageType.CLIENT  # Por defecto
        }
        self.message_type = type_mapping.get(self.sender, MessageType.CLIENT)
    
    def mark_processed(self):
        """Marca el mensaje como procesado."""
        self.is_processed = True
        self.processed_at = datetime.now()
    
    def mark_sent(self):
        """Marca el mensaje como enviado."""
        self.is_sent = True
    
    def set_robot_state(self, state: RobotState):
        """
        Establece el estado del robot para el mensaje.
        
        Args:
            state: Estado emocional del robot
        """
        self.robot_state = state
        self.add_metadata('robot_state', state.value)
    
    def add_metadata(self, key: str, value: Any):
        """
        Agrega metadatos al mensaje.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato del mensaje.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del metadato o default
        """
        return self.metadata.get(key, default)
    
    def get_display_text(self, max_length: int = None) -> str:
        """
        Obtiene el texto para mostrar, opcionalmente truncado.
        
        Args:
            max_length: Longitud máxima del texto
            
        Returns:
            Texto para mostrar
        """
        if max_length and len(self.text) > max_length:
            return self.text[:max_length - 3] + "..."
        return self.text
    
    def get_sender_display_name(self) -> str:
        """
        Obtiene el nombre para mostrar del remitente.
        
        Returns:
            Nombre del remitente para mostrar
        """
        names = {
            MessageSender.CLIENT: "Usuario",
            MessageSender.ROBOT: "SHARA",
            MessageSender.WIZARD: "Operador",
            MessageSender.SYSTEM: "Sistema"
        }
        return names.get(self.sender, "Desconocido")
    
    def is_from_user(self) -> bool:
        """
        Verifica si el mensaje proviene del usuario.
        
        Returns:
            True si es del usuario
        """
        return self.sender == MessageSender.CLIENT
    
    def is_from_robot(self) -> bool:
        """
        Verifica si el mensaje proviene del robot.
        
        Returns:
            True si es del robot
        """
        return self.sender == MessageSender.ROBOT
    
    def is_from_wizard(self) -> bool:
        """
        Verifica si el mensaje proviene del wizard/operador.
        
        Returns:
            True si es del wizard
        """
        return self.sender == MessageSender.WIZARD
    
    def is_system_message(self) -> bool:
        """
        Verifica si el mensaje es del sistema.
        
        Returns:
            True si es del sistema
        """
        return self.sender == MessageSender.SYSTEM
    
    def get_age_seconds(self) -> float:
        """
        Obtiene la edad del mensaje en segundos.
        
        Returns:
            Edad en segundos
        """
        return (datetime.now() - self.timestamp).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el mensaje a diccionario.
        
        Returns:
            Representación en diccionario del mensaje
        """
        return {
            'message_id': self.message_id,
            'text': self.text,
            'sender': self.sender.value,
            'message_type': self.message_type.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'robot_state': self.robot_state.value if self.robot_state else None,
            'metadata': self.metadata,
            'is_processed': self.is_processed,
            'is_sent': self.is_sent,
            'requires_response': self.requires_response,
            'display_text': self.get_display_text(50),
            'sender_display_name': self.get_sender_display_name(),
            'age_seconds': self.get_age_seconds()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Crea un mensaje desde un diccionario.
        
        Args:
            data: Datos del mensaje en formato diccionario
            
        Returns:
            Instancia de Message
        """
        # Parsear fechas
        timestamp = datetime.now()
        if data.get('timestamp'):
            try:
                timestamp = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                pass
        
        processed_at = None
        if data.get('processed_at'):
            try:
                processed_at = datetime.fromisoformat(data['processed_at'])
            except ValueError:
                pass
        
        # Parsear enums
        sender = MessageSender.CLIENT
        if data.get('sender'):
            try:
                sender = MessageSender(data['sender'])
            except ValueError:
                pass
        
        message_type = MessageType.CLIENT
        if data.get('message_type'):
            try:
                message_type = MessageType(data['message_type'])
            except ValueError:
                pass
        
        robot_state = None
        if data.get('robot_state'):
            try:
                robot_state = RobotState(data['robot_state'])
            except ValueError:
                pass
        
        return cls(
            message_id=data.get('message_id', str(uuid.uuid4())),
            text=data['text'],
            sender=sender,
            message_type=message_type,
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            timestamp=timestamp,
            processed_at=processed_at,
            robot_state=robot_state,
            metadata=data.get('metadata', {}),
            is_processed=data.get('is_processed', False),
            is_sent=data.get('is_sent', False),
            requires_response=data.get('requires_response', False)
        )
    
    @classmethod
    def create_client_message(cls, text: str, user_id: str = None, session_id: str = None) -> 'Message':
        """
        Crea un mensaje del cliente.
        
        Args:
            text: Texto del mensaje
            user_id: ID del usuario
            session_id: ID de la sesión
            
        Returns:
            Instancia de Message
        """
        return cls(
            text=text,
            sender=MessageSender.CLIENT,
            message_type=MessageType.CLIENT,
            user_id=user_id,
            session_id=session_id,
            requires_response=True
        )
    
    @classmethod
    def create_robot_message(cls, text: str, robot_state: RobotState = None, 
                           user_id: str = None, session_id: str = None) -> 'Message':
        """
        Crea un mensaje del robot.
        
        Args:
            text: Texto del mensaje
            robot_state: Estado emocional del robot
            user_id: ID del usuario
            session_id: ID de la sesión
            
        Returns:
            Instancia de Message
        """
        message = cls(
            text=text,
            sender=MessageSender.ROBOT,
            message_type=MessageType.ROBOT,
            user_id=user_id,
            session_id=session_id
        )
        
        if robot_state:
            message.set_robot_state(robot_state)
        
        return message
    
    @classmethod
    def create_wizard_message(cls, text: str, robot_state: RobotState = None,
                            user_id: str = None, session_id: str = None) -> 'Message':
        """
        Crea un mensaje del wizard/operador.
        
        Args:
            text: Texto del mensaje
            robot_state: Estado emocional del robot
            user_id: ID del usuario
            session_id: ID de la sesión
            
        Returns:
            Instancia de Message
        """
        message = cls(
            text=text,
            sender=MessageSender.WIZARD,
            message_type=MessageType.WIZARD,
            user_id=user_id,
            session_id=session_id
        )
        
        if robot_state:
            message.set_robot_state(robot_state)
        
        return message
    
    def __str__(self) -> str:
        """Representación en string del mensaje."""
        return f"Message({self.sender.value}: {self.get_display_text(30)})"
    
    def __repr__(self) -> str:
        """Representación detallada del mensaje."""
        return (
            f"Message(id='{self.message_id}', "
            f"sender={self.sender.value}, "
            f"type={self.message_type.value}, "
            f"text='{self.get_display_text(20)}')"
        )