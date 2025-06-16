"""
Sistema de validadores para SHARA Wizard
"""

import re
import socket
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from pathlib import Path

from config import RobotState, OperationMode, MessageType
from utils.logger import get_logger

logger = get_logger(__name__)

class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error in '{field}': {message}")

class ValidationResult:
    """Resultado de una validación."""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, 
                 warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Agrega un error al resultado."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Agrega una advertencia al resultado."""
        self.warnings.append(warning)
    
    def __bool__(self):
        """Permite usar el resultado como booleano."""
        return self.is_valid
    
    def __str__(self):
        """Representación en string del resultado."""
        if self.is_valid:
            return "Validación exitosa"
        
        result = "Errores de validación:\n"
        for error in self.errors:
            result += f"  - {error}\n"
        
        if self.warnings:
            result += "Advertencias:\n"
            for warning in self.warnings:
                result += f"  - {warning}\n"
        
        return result.strip()

class BaseValidator:
    """Clase base para todos los validadores."""
    
    def __init__(self, required: bool = True, allow_empty: bool = False):
        self.required = required
        self.allow_empty = allow_empty
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        """
        Valida un valor.
        
        Args:
            value: Valor a validar
            field_name: Nombre del campo para mensajes de error
            
        Returns:
            Resultado de la validación
        """
        result = ValidationResult()
        
        # Validaciones básicas
        if value is None:
            if self.required:
                result.add_error(f"{field_name} es requerido")
            return result
        
        if isinstance(value, str) and not value.strip():
            if self.required and not self.allow_empty:
                result.add_error(f"{field_name} no puede estar vacío")
            return result
        
        # Validación específica del validador
        return self._validate_specific(value, field_name, result)
    
    def _validate_specific(self, value: Any, field_name: str, 
                          result: ValidationResult) -> ValidationResult:
        """
        Implementación específica de validación.
        Debe ser sobrescrita por las clases hijas.
        """
        return result

class StringValidator(BaseValidator):
    """Validador para strings."""
    
    def __init__(self, min_length: int = 0, max_length: int = None,
                 pattern: str = None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        # Validar longitud mínima
        if len(value) < self.min_length:
            result.add_error(f"{field_name} debe tener al menos {self.min_length} caracteres")
        
        # Validar longitud máxima
        if self.max_length and len(value) > self.max_length:
            result.add_error(f"{field_name} no puede tener más de {self.max_length} caracteres")
        
        # Validar patrón
        if self.pattern and not self.pattern.match(value):
            result.add_error(f"{field_name} no cumple con el formato requerido")
        
        return result

class URLValidator(BaseValidator):
    """Validador para URLs."""
    
    def __init__(self, schemes: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.schemes = schemes or ['http', 'https']
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        try:
            parsed = urlparse(value)
            
            # Validar esquema
            if parsed.scheme not in self.schemes:
                result.add_error(f"{field_name} debe usar uno de estos esquemas: {', '.join(self.schemes)}")
            
            # Validar que tenga dominio
            if not parsed.netloc:
                result.add_error(f"{field_name} debe incluir un dominio válido")
            
            # Validar conectividad (opcional, con timeout)
            if result.is_valid:
                try:
                    socket.setdefaulttimeout(5)
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((parsed.hostname, parsed.port or 80))
                except (socket.error, socket.timeout):
                    result.add_warning(f"No se pudo verificar la conectividad a {value}")
                
        except Exception as e:
            result.add_error(f"{field_name} no es una URL válida: {str(e)}")
        
        return result

class EnumValidator(BaseValidator):
    """Validador para enums."""
    
    def __init__(self, enum_class, **kwargs):
        super().__init__(**kwargs)
        self.enum_class = enum_class
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        # Si ya es una instancia del enum, es válido
        if isinstance(value, self.enum_class):
            return result
        
        # Si es un string, intentar convertir
        if isinstance(value, str):
            try:
                self.enum_class(value)
                return result
            except ValueError:
                valid_values = [e.value for e in self.enum_class]
                result.add_error(f"{field_name} debe ser uno de: {', '.join(valid_values)}")
        else:
            result.add_error(f"{field_name} debe ser un valor válido del enum {self.enum_class.__name__}")
        
        return result

class FilePathValidator(BaseValidator):
    """Validador para rutas de archivo."""
    
    def __init__(self, must_exist: bool = False, must_be_file: bool = True,
                 allowed_extensions: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.must_exist = must_exist
        self.must_be_file = must_be_file
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        if not isinstance(value, (str, Path)):
            result.add_error(f"{field_name} debe ser una ruta de archivo válida")
            return result
        
        path = Path(value)
        
        # Validar existencia
        if self.must_exist and not path.exists():
            result.add_error(f"El archivo {value} no existe")
            return result
        
        # Validar que sea archivo
        if self.must_exist and self.must_be_file and not path.is_file():
            result.add_error(f"{value} no es un archivo válido")
        
        # Validar extensión
        if self.allowed_extensions and path.suffix.lower() not in self.allowed_extensions:
            result.add_error(f"El archivo debe tener una de estas extensiones: {', '.join(self.allowed_extensions)}")
        
        return result

class DictValidator(BaseValidator):
    """Validador para diccionarios con esquema."""
    
    def __init__(self, schema: Dict[str, BaseValidator], strict: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.schema = schema
        self.strict = strict  # Si True, no permite campos extra
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        if not isinstance(value, dict):
            result.add_error(f"{field_name} debe ser un diccionario")
            return result
        
        # Validar campos requeridos
        for key, validator in self.schema.items():
            field_result = validator.validate(value.get(key), f"{field_name}.{key}")
            
            if not field_result.is_valid:
                result.errors.extend(field_result.errors)
                result.is_valid = False
            
            result.warnings.extend(field_result.warnings)
        
        # Validar campos extra si es estricto
        if self.strict:
            extra_fields = set(value.keys()) - set(self.schema.keys())
            if extra_fields:
                result.add_warning(f"Campos no reconocidos en {field_name}: {', '.join(extra_fields)}")
        
        return result

class MessageValidator(DictValidator):
    """Validador específico para mensajes."""
    
    def __init__(self, **kwargs):
        schema = {
            'text': StringValidator(min_length=1, max_length=5000, required=True),
            'sender': EnumValidator(MessageType, required=True),
            'user_id': StringValidator(required=False, allow_empty=True),
            'session_id': StringValidator(required=False, allow_empty=True),
            'robot_state': EnumValidator(RobotState, required=False)
        }
        super().__init__(schema, **kwargs)

class ConfigValidator(DictValidator):
    """Validador para configuración de la aplicación."""
    
    def __init__(self, **kwargs):
        schema = {
            'server_url': URLValidator(required=True),
            'web_url': URLValidator(required=True),
            'operation_mode': EnumValidator(OperationMode, required=False),
            'log_level': StringValidator(pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$', required=False),
            'window_width': IntegerValidator(min_value=800, max_value=3840, required=False),
            'window_height': IntegerValidator(min_value=600, max_value=2160, required=False)
        }
        super().__init__(schema, **kwargs)

class IntegerValidator(BaseValidator):
    """Validador para números enteros."""
    
    def __init__(self, min_value: int = None, max_value: int = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        # Intentar convertir a entero
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                result.add_error(f"{field_name} debe ser un número entero")
                return result
        except ValueError:
            result.add_error(f"{field_name} debe ser un número entero válido")
            return result
        
        # Validar rango
        if self.min_value is not None and value < self.min_value:
            result.add_error(f"{field_name} debe ser mayor o igual a {self.min_value}")
        
        if self.max_value is not None and value > self.max_value:
            result.add_error(f"{field_name} debe ser menor o igual a {self.max_value}")
        
        return result

class ListValidator(BaseValidator):
    """Validador para listas."""
    
    def __init__(self, item_validator: BaseValidator, min_length: int = 0,
                 max_length: int = None, **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
    
    def _validate_specific(self, value: Any, field_name: str,
                          result: ValidationResult) -> ValidationResult:
        if not isinstance(value, list):
            result.add_error(f"{field_name} debe ser una lista")
            return result
        
        # Validar longitud
        if len(value) < self.min_length:
            result.add_error(f"{field_name} debe tener al menos {self.min_length} elementos")
        
        if self.max_length and len(value) > self.max_length:
            result.add_error(f"{field_name} no puede tener más de {self.max_length} elementos")
        
        # Validar cada elemento
        for i, item in enumerate(value):
            item_result = self.item_validator.validate(item, f"{field_name}[{i}]")
            
            if not item_result.is_valid:
                result.errors.extend(item_result.errors)
                result.is_valid = False
            
            result.warnings.extend(item_result.warnings)
        
        return result

# Funciones de conveniencia para validaciones comunes
def validate_message(message_data: Dict[str, Any]) -> ValidationResult:
    """
    Valida datos de mensaje.
    
    Args:
        message_data: Datos del mensaje a validar
        
    Returns:
        Resultado de la validación
    """
    validator = MessageValidator()
    return validator.validate(message_data, "message")

def validate_config(config_data: Dict[str, Any]) -> ValidationResult:
    """
    Valida configuración de la aplicación.
    
    Args:
        config_data: Datos de configuración a validar
        
    Returns:
        Resultado de la validación
    """
    validator = ConfigValidator()
    return validator.validate(config_data, "config")

def validate_url(url: str, field_name: str = "URL") -> ValidationResult:
    """
    Valida una URL.
    
    Args:
        url: URL a validar
        field_name: Nombre del campo para mensajes
        
    Returns:
        Resultado de la validación
    """
    validator = URLValidator()
    return validator.validate(url, field_name)

def validate_robot_state(state: Union[str, RobotState], 
                        field_name: str = "robot_state") -> ValidationResult:
    """
    Valida un estado del robot.
    
    Args:
        state: Estado a validar
        field_name: Nombre del campo para mensajes
        
    Returns:
        Resultado de la validación
    """
    validator = EnumValidator(RobotState)
    return validator.validate(state, field_name)

def validate_file_path(file_path: Union[str, Path], must_exist: bool = False,
                      allowed_extensions: List[str] = None,
                      field_name: str = "file_path") -> ValidationResult:
    """
    Valida una ruta de archivo.
    
    Args:
        file_path: Ruta a validar
        must_exist: Si el archivo debe existir
        allowed_extensions: Extensiones permitidas
        field_name: Nombre del campo para mensajes
        
    Returns:
        Resultado de la validación
    """
    validator = FilePathValidator(must_exist=must_exist, allowed_extensions=allowed_extensions)
    return validator.validate(file_path, field_name)

def validate_text_input(text: str, min_length: int = 1, max_length: int = 1000,
                       field_name: str = "text") -> ValidationResult:
    """
    Valida entrada de texto.
    
    Args:
        text: Texto a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
        field_name: Nombre del campo para mensajes
        
    Returns:
        Resultado de la validación
    """
    validator = StringValidator(min_length=min_length, max_length=max_length)
    return validator.validate(text, field_name)

# Validaciones específicas para SHARA
def validate_user_id(user_id: str) -> ValidationResult:
    """Valida un ID de usuario."""
    validator = StringValidator(min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    return validator.validate(user_id, "user_id")

def validate_session_id(session_id: str) -> ValidationResult:
    """Valida un ID de sesión."""
    validator = StringValidator(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    return validator.validate(session_id, "session_id")

def validate_server_response(response_data: Dict[str, Any]) -> ValidationResult:
    """
    Valida respuesta del servidor.
    
    Args:
        response_data: Datos de respuesta a validar
        
    Returns:
        Resultado de la validación
    """
    schema = {
        'success': BaseValidator(required=True),
        'data': BaseValidator(required=False, allow_empty=True),
        'error': StringValidator(required=False, allow_empty=True),
        'timestamp': StringValidator(required=False)
    }
    
    validator = DictValidator(schema)
    return validator.validate(response_data, "server_response")