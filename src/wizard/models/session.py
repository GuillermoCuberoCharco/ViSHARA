"""
Modelo de sesión para SHARA Wizard
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

from .message import Message
from .user import User

class SessionStatus(Enum):
    """Estados posibles de una sesión."""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"

@dataclass
class Session:
    """
    Modelo que representa una sesión de conversación.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Metadatos temporales
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Contenido de la sesión
    messages: List[Message] = field(default_factory=list)
    user_info: Optional[User] = None
    
    # Estadísticas
    message_count: int = 0
    user_messages_count: int = 0
    robot_messages_count: int = 0
    wizard_messages_count: int = 0
    
    # Configuración
    max_messages: int = 1000
    auto_save: bool = True
    
    # Metadatos adicionales
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicialización post-creación."""
        if self.started_at is None:
            self.started_at = self.created_at
        
        # Actualizar contadores si ya hay mensajes
        self._update_message_counts()
    
    def start(self):
        """Inicia la sesión."""
        if self.status == SessionStatus.ACTIVE:
            return
        
        self.status = SessionStatus.ACTIVE
        self.started_at = datetime.now()
        self.last_activity = self.started_at
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Sesión {self.session_id} iniciada")
    
    def pause(self):
        """Pausa la sesión."""
        if self.status != SessionStatus.ACTIVE:
            return
        
        self.status = SessionStatus.PAUSED
        self.last_activity = datetime.now()
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Sesión {self.session_id} pausada")
    
    def end(self):
        """Finaliza la sesión."""
        if self.status == SessionStatus.ENDED:
            return
        
        self.status = SessionStatus.ENDED
        self.ended_at = datetime.now()
        self.last_activity = self.ended_at
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Sesión {self.session_id} finalizada")
    
    def add_message(self, message: Message) -> bool:
        """
        Agrega un mensaje a la sesión.
        
        Args:
            message: Mensaje a agregar
            
        Returns:
            True si se agregó correctamente
        """
        if self.status != SessionStatus.ACTIVE:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Intento de agregar mensaje a sesión inactiva {self.session_id}")
            return False
        
        # Verificar límite de mensajes
        if len(self.messages) >= self.max_messages:
            # Remover mensajes más antiguos
            self.messages = self.messages[-(self.max_messages - 1):]
        
        # Configurar el mensaje
        message.session_id = self.session_id
        if self.user_id:
            message.user_id = self.user_id
        
        # Agregar mensaje
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        # Actualizar contadores
        self._update_message_counts()
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Mensaje agregado a sesión {self.session_id}: {message.sender.value}")
        
        return True
    
    def get_messages(self, limit: Optional[int] = None, 
                    sender: Optional[str] = None) -> List[Message]:
        """
        Obtiene mensajes de la sesión.
        
        Args:
            limit: Límite de mensajes a devolver
            sender: Filtrar por remitente específico
            
        Returns:
            Lista de mensajes
        """
        messages = self.messages
        
        # Filtrar por remitente si se especifica
        if sender:
            from .message import MessageSender
            try:
                sender_enum = MessageSender(sender)
                messages = [m for m in messages if m.sender == sender_enum]
            except ValueError:
                pass
        
        # Aplicar límite
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_last_message(self, sender: Optional[str] = None) -> Optional[Message]:
        """
        Obtiene el último mensaje de la sesión.
        
        Args:
            sender: Filtrar por remitente específico
            
        Returns:
            Último mensaje o None
        """
        messages = self.get_messages(sender=sender)
        return messages[-1] if messages else None
    
    def set_user(self, user: User):
        """
        Asocia un usuario a la sesión.
        
        Args:
            user: Usuario a asociar
        """
        self.user_info = user
        self.user_id = user.user_id
        
        # Actualizar mensajes existentes
        for message in self.messages:
            if not message.user_id:
                message.user_id = self.user_id
        
        self.last_activity = datetime.now()
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Usuario {user.user_id} asociado a sesión {self.session_id}")
    
    def _update_message_counts(self):
        """Actualiza los contadores de mensajes."""
        from .message import MessageSender
        
        self.message_count = len(self.messages)
        self.user_messages_count = len([m for m in self.messages if m.sender == MessageSender.CLIENT])
        self.robot_messages_count = len([m for m in self.messages if m.sender == MessageSender.ROBOT])
        self.wizard_messages_count = len([m for m in self.messages if m.sender == MessageSender.WIZARD])
    
    def get_duration(self) -> Optional[float]:
        """
        Obtiene la duración de la sesión en segundos.
        
        Returns:
            Duración en segundos o None si no ha iniciado
        """
        if not self.started_at:
            return None
        
        end_time = self.ended_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def get_activity_age(self) -> float:
        """
        Obtiene el tiempo desde la última actividad en segundos.
        
        Returns:
            Tiempo en segundos desde la última actividad
        """
        return (datetime.now() - self.last_activity).total_seconds()
    
    def is_active(self) -> bool:
        """
        Verifica si la sesión está activa.
        
        Returns:
            True si la sesión está activa
        """
        return self.status == SessionStatus.ACTIVE
    
    def is_expired(self, timeout_seconds: int = 1800) -> bool:  # 30 minutos por defecto
        """
        Verifica si la sesión ha expirado por inactividad.
        
        Args:
            timeout_seconds: Tiempo de expiración en segundos
            
        Returns:
            True si la sesión ha expirado
        """
        return self.get_activity_age() > timeout_seconds
    
    def add_metadata(self, key: str, value: Any):
        """
        Agrega metadatos a la sesión.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self.metadata[key] = value
        self.last_activity = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato de la sesión.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del metadato o default
        """
        return self.metadata.get(key, default)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la sesión.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'status': self.status.value,
            'duration_seconds': self.get_duration(),
            'activity_age_seconds': self.get_activity_age(),
            'total_messages': self.message_count,
            'user_messages': self.user_messages_count,
            'robot_messages': self.robot_messages_count,
            'wizard_messages': self.wizard_messages_count,
            'is_active': self.is_active(),
            'has_user': self.user_info is not None,
            'user_identified': self.user_info.is_identified() if self.user_info else False
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la sesión a diccionario.
        
        Returns:
            Representación en diccionario de la sesión
        """
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'last_activity': self.last_activity.isoformat(),
            'messages': [m.to_dict() for m in self.messages],
            'user_info': self.user_info.to_dict() if self.user_info else None,
            'message_count': self.message_count,
            'user_messages_count': self.user_messages_count,
            'robot_messages_count': self.robot_messages_count,
            'wizard_messages_count': self.wizard_messages_count,
            'max_messages': self.max_messages,
            'auto_save': self.auto_save,
            'metadata': self.metadata,
            'stats': self.get_stats()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """
        Crea una sesión desde un diccionario.
        
        Args:
            data: Datos de la sesión en formato diccionario
            
        Returns:
            Instancia de Session
        """
        # Parsear fechas
        created_at = datetime.now()
        if data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(data['created_at'])
            except ValueError:
                pass
        
        started_at = None
        if data.get('started_at'):
            try:
                started_at = datetime.fromisoformat(data['started_at'])
            except ValueError:
                pass
        
        ended_at = None
        if data.get('ended_at'):
            try:
                ended_at = datetime.fromisoformat(data['ended_at'])
            except ValueError:
                pass
        
        last_activity = created_at
        if data.get('last_activity'):
            try:
                last_activity = datetime.fromisoformat(data['last_activity'])
            except ValueError:
                pass
        
        # Parsear estado
        status = SessionStatus.ACTIVE
        if data.get('status'):
            try:
                status = SessionStatus(data['status'])
            except ValueError:
                pass
        
        # Parsear mensajes
        messages = []
        if data.get('messages'):
            for msg_data in data['messages']:
                try:
                    messages.append(Message.from_dict(msg_data))
                except Exception:
                    continue
        
        # Parsear usuario
        user_info = None
        if data.get('user_info'):
            try:
                user_info = User.from_dict(data['user_info'])
            except Exception:
                pass
        
        return cls(
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=data.get('user_id'),
            status=status,
            created_at=created_at,
            started_at=started_at,
            ended_at=ended_at,
            last_activity=last_activity,
            messages=messages,
            user_info=user_info,
            max_messages=data.get('max_messages', 1000),
            auto_save=data.get('auto_save', True),
            metadata=data.get('metadata', {})
        )
    
    def __str__(self) -> str:
        """Representación en string de la sesión."""
        return f"Session({self.session_id}, {self.status.value}, {self.message_count} mensajes)"
    
    def __repr__(self) -> str:
        """Representación detallada de la sesión."""
        return (
            f"Session(id='{self.session_id}', "
            f"user_id='{self.user_id}', "
            f"status={self.status.value}, "
            f"messages={self.message_count})"
        )