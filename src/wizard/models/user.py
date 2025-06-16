"""
Modelo de usuario para SHARA Wizard
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class UserStatus(Enum):
    """Estados posibles del usuario."""
    UNKNOWN = "unknown"
    DETECTED = "detected"
    IDENTIFIED = "identified"
    LOST = "lost"

@dataclass
class User:
    """
    Modelo que representa un usuario del sistema.
    """
    user_id: str
    user_name: Optional[str] = None
    status: UserStatus = UserStatus.UNKNOWN
    is_new_user: bool = False
    needs_identification: bool = True
    confidence: float = 0.0
    consensus_ratio: float = 0.0
    
    # Metadatos temporales
    detected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    session_id: Optional[str] = None
    
    # Información adicional
    total_visits: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicialización post-creación."""
        if self.detected_at is None:
            self.detected_at = datetime.now()
        
        if self.last_seen is None:
            self.last_seen = self.detected_at
    
    def update_status(self, new_status: UserStatus):
        """
        Actualiza el estado del usuario.
        
        Args:
            new_status: Nuevo estado del usuario
        """
        old_status = self.status
        self.status = new_status
        self.last_seen = datetime.now()
        
        # Log del cambio de estado
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Usuario {self.user_id}: {old_status.value} -> {new_status.value}")
    
    def identify(self, name: str):
        """
        Identifica al usuario con un nombre.
        
        Args:
            name: Nombre del usuario
        """
        self.user_name = name
        self.needs_identification = False
        self.status = UserStatus.IDENTIFIED
        self.last_seen = datetime.now()
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Usuario {self.user_id} identificado como '{name}'")
    
    def update_confidence(self, confidence: float, consensus_ratio: float = None):
        """
        Actualiza la confianza de detección del usuario.
        
        Args:
            confidence: Nivel de confianza (0.0 - 1.0)
            consensus_ratio: Ratio de consenso en detección
        """
        self.confidence = max(0.0, min(1.0, confidence))
        if consensus_ratio is not None:
            self.consensus_ratio = max(0.0, min(1.0, consensus_ratio))
        
        self.last_seen = datetime.now()
    
    def is_identified(self) -> bool:
        """
        Verifica si el usuario está identificado.
        
        Returns:
            True si el usuario tiene nombre y está identificado
        """
        return (
            self.user_name is not None and 
            self.user_name != "unknown" and 
            not self.needs_identification
        )
    
    def is_present(self) -> bool:
        """
        Verifica si el usuario está presente (detectado o identificado).
        
        Returns:
            True si el usuario está presente
        """
        return self.status in [UserStatus.DETECTED, UserStatus.IDENTIFIED]
    
    def get_display_name(self) -> str:
        """
        Obtiene el nombre para mostrar del usuario.
        
        Returns:
            Nombre del usuario o ID si no tiene nombre
        """
        if self.is_identified():
            return self.user_name
        return f"Usuario {self.user_id}"
    
    def add_metadata(self, key: str, value: Any):
        """
        Agrega metadatos al usuario.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato del usuario.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del metadato o default
        """
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el usuario a diccionario.
        
        Returns:
            Representación en diccionario del usuario
        """
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'status': self.status.value,
            'is_new_user': self.is_new_user,
            'needs_identification': self.needs_identification,
            'confidence': self.confidence,
            'consensus_ratio': self.consensus_ratio,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'session_id': self.session_id,
            'total_visits': self.total_visits,
            'metadata': self.metadata,
            'is_identified': self.is_identified(),
            'is_present': self.is_present(),
            'display_name': self.get_display_name()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Crea un usuario desde un diccionario.
        
        Args:
            data: Datos del usuario en formato diccionario
            
        Returns:
            Instancia de User
        """
        # Parsear fechas
        detected_at = None
        if data.get('detected_at'):
            detected_at = datetime.fromisoformat(data['detected_at'])
        
        last_seen = None
        if data.get('last_seen'):
            last_seen = datetime.fromisoformat(data['last_seen'])
        
        # Parsear estado
        status = UserStatus.UNKNOWN
        if data.get('status'):
            try:
                status = UserStatus(data['status'])
            except ValueError:
                pass
        
        return cls(
            user_id=data['user_id'],
            user_name=data.get('user_name'),
            status=status,
            is_new_user=data.get('is_new_user', False),
            needs_identification=data.get('needs_identification', True),
            confidence=data.get('confidence', 0.0),
            consensus_ratio=data.get('consensus_ratio', 0.0),
            detected_at=detected_at,
            last_seen=last_seen,
            session_id=data.get('session_id'),
            total_visits=data.get('total_visits', 0),
            metadata=data.get('metadata', {})
        )
    
    def __str__(self) -> str:
        """Representación en string del usuario."""
        return f"User({self.user_id}, {self.get_display_name()}, {self.status.value})"
    
    def __repr__(self) -> str:
        """Representación detallada del usuario."""
        return (
            f"User(user_id='{self.user_id}', "
            f"user_name='{self.user_name}', "
            f"status={self.status.value}, "
            f"is_identified={self.is_identified()})"
        )