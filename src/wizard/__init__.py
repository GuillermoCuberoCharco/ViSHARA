"""
SHARA Wizard of Oz Interface

Una aplicación PyQt6 para operar como interfaz de operador (Wizard of Oz)
para el robot social SHARA, permitiendo supervisión y control manual/automático
de las interacciones con usuarios.

Características principales:
- Interfaz de chat para comunicación con usuarios
- Vista de cámara en tiempo real del usuario
- Navegador web integrado para la interfaz del usuario
- Modo manual y automático de operación
- Gestión de estados emocionales del robot
- Sistema de logging avanzado
- Validación robusta de datos
- Arquitectura modular y escalable

Autores: Guillermo Cubero Charco
Versión: 2.0.0
"""

__version__ = "2.0.0"
__title__ = "SHARA Wizard of Oz Interface"
__description__ = "Interfaz de operador para el robot social SHARA"
__author__ = "Guillermo Cubero Charco"
__email__ = "Guillermo.Cubero@uclm.es"
__license__ = "MIT"
__url__ = "https://github.com/GuillermoCuberoCharco/ViSHARA"

# Importaciones principales
from .core import SharaWizardApp, EventManager
from .config import settings, RobotState, OperationMode, MessageType
from .utils import get_logger

# Configurar logger principal
logger = get_logger(__name__)

def get_version():
    """Obtiene la versión de la aplicación."""
    return __version__

def get_app_info():
    """
    Obtiene información de la aplicación.
    
    Returns:
        Diccionario con información de la aplicación
    """
    return {
        'name': __title__,
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'email': __email__,
        'license': __license__,
        'url': __url__
    }

# Validar configuración al importar
def _validate_environment():
    """Valida el entorno y configuración básica."""
    try:
        from .utils import validate_config
        
        # Validar configuración básica
        config_data = {
            'server_url': settings.server.url,
            'web_url': settings.server.web_url,
            'log_level': settings.logging.level
        }
        
        result = validate_config(config_data)
        if not result:
            logger.warning(f"Problemas de configuración detectados:\n{result}")
        
    except Exception as e:
        logger.error(f"Error validando entorno: {e}")

# Ejecutar validación al importar
_validate_environment()

# Mensaje de bienvenida
logger.info(f"{__title__} v{__version__} - Sistema inicializado")

__all__ = [
    # Información del proyecto
    '__version__',
    '__title__',
    '__description__',
    '__author__',
    'get_version',
    'get_app_info',
    
    # Componentes principales
    'SharaWizardApp',
    'EventManager',
    'settings',
    'RobotState',
    'OperationMode', 
    'MessageType',
    'get_logger'
]