"""
Sistema de logging para SHARA Wizard
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from config.settings import settings, LOGS_DIR

class ColoredFormatter(logging.Formatter):
    """Formatter que agrega colores a los logs en consola."""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Aplicar color al nivel de log
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Colorear el nombre del módulo
        record.name = f"\033[94m{record.name}{self.COLORS['RESET']}"
        
        return super().format(record)

class SharaLogger:
    """Configurador de logging para SHARA Wizard."""
    
    def __init__(self):
        self.loggers = {}
        self.handlers_configured = False
        
    def setup_logger(self, name: Optional[str] = None, 
                    level: Optional[str] = None,
                    file_output: bool = True,
                    console_output: bool = True) -> logging.Logger:
        """
        Configura y retorna un logger.
        
        Args:
            name: Nombre del logger (None para root)
            level: Nivel de logging
            file_output: Si escribir a archivo
            console_output: Si escribir a consola
            
        Returns:
            Logger configurado
        """
        logger_name = name or 'shara_wizard'
        
        # Si ya existe, retornarlo
        if logger_name in self.loggers:
            return self.loggers[logger_name]
        
        # Crear logger
        logger = logging.getLogger(logger_name)
        
        # Configurar nivel
        log_level = level or settings.logging.level
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Evitar duplicación de handlers
        if not logger.handlers or not self.handlers_configured:
            # Handler para consola
            if console_output:
                console_handler = self._create_console_handler()
                logger.addHandler(console_handler)
            
            # Handler para archivo
            if file_output:
                file_handler = self._create_file_handler()
                if file_handler:
                    logger.addHandler(file_handler)
            
            # Handler para archivo de errores
            if file_output:
                error_handler = self._create_error_handler()
                if error_handler:
                    logger.addHandler(error_handler)
        
        # Evitar propagación al logger padre para evitar duplicados
        logger.propagate = False
        
        self.loggers[logger_name] = logger
        self.handlers_configured = True
        
        return logger
    
    def _create_console_handler(self) -> logging.StreamHandler:
        """Crea handler para salida de consola."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Formatter con colores para consola
        console_formatter = ColoredFormatter(
            fmt=settings.logging.format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        return console_handler
    
    def _create_file_handler(self) -> Optional[logging.handlers.RotatingFileHandler]:
        """Crea handler para archivo de log."""
        try:
            # Asegurar que el directorio existe
            LOGS_DIR.mkdir(exist_ok=True)
            
            # Archivo de log principal
            log_file = LOGS_DIR / 'shara_wizard.log'
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=settings.logging.max_bytes,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter sin colores para archivo
            file_formatter = logging.Formatter(
                fmt=settings.logging.format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            return file_handler
            
        except Exception as e:
            print(f"Error configurando archivo de log: {e}")
            return None
    
    def _create_error_handler(self) -> Optional[logging.handlers.RotatingFileHandler]:
        """Crea handler específico para errores."""
        try:
            # Archivo específico para errores
            error_file = LOGS_DIR / 'shara_wizard_errors.log'
            
            error_handler = logging.handlers.RotatingFileHandler(
                error_file,
                maxBytes=settings.logging.max_bytes,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            
            # Formatter detallado para errores
            error_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            error_handler.setFormatter(error_formatter)
            
            return error_handler
            
        except Exception as e:
            print(f"Error configurando archivo de errores: {e}")
            return None
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtiene un logger existente o crea uno nuevo.
        
        Args:
            name: Nombre del logger
            
        Returns:
            Logger solicitado
        """
        if name in self.loggers:
            return self.loggers[name]
        
        return self.setup_logger(name)
    
    def set_level(self, level: str, logger_name: Optional[str] = None):
        """
        Cambia el nivel de logging.
        
        Args:
            level: Nuevo nivel ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            logger_name: Nombre del logger (None para todos)
        """
        try:
            log_level = getattr(logging, level.upper())
            
            if logger_name:
                if logger_name in self.loggers:
                    self.loggers[logger_name].setLevel(log_level)
            else:
                # Cambiar nivel para todos los loggers
                for logger in self.loggers.values():
                    logger.setLevel(log_level)
                    
        except AttributeError:
            print(f"Nivel de log inválido: {level}")
    
    def add_file_handler(self, logger_name: str, filename: str, 
                        level: str = 'INFO', max_bytes: int = None):
        """
        Agrega un handler de archivo específico a un logger.
        
        Args:
            logger_name: Nombre del logger
            filename: Nombre del archivo
            level: Nivel de logging para este handler
            max_bytes: Tamaño máximo del archivo
        """
        try:
            if logger_name not in self.loggers:
                self.setup_logger(logger_name)
            
            logger = self.loggers[logger_name]
            log_file = LOGS_DIR / filename
            
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes or settings.logging.max_bytes,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            
            handler.setLevel(getattr(logging, level.upper()))
            
            formatter = logging.Formatter(
                fmt=settings.logging.format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
            
        except Exception as e:
            print(f"Error agregando handler de archivo: {e}")
    
    def create_session_logger(self, session_id: str) -> logging.Logger:
        """
        Crea un logger específico para una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Logger de la sesión
        """
        logger_name = f"session_{session_id}"
        logger = self.setup_logger(logger_name, file_output=False)
        
        # Agregar handler específico para la sesión
        self.add_file_handler(
            logger_name, 
            f"session_{session_id}.log",
            level='DEBUG'
        )
        
        return logger
    
    def log_system_info(self, logger: logging.Logger):
        """
        Registra información del sistema.
        
        Args:
            logger: Logger a usar
        """
        import platform
        import sys
        
        logger.info("=== INFORMACIÓN DEL SISTEMA ===")
        logger.info(f"Sistema operativo: {platform.system()} {platform.release()}")
        logger.info(f"Versión de Python: {sys.version}")
        logger.info(f"Plataforma: {platform.platform()}")
        logger.info(f"Arquitectura: {platform.architecture()}")
        logger.info(f"Procesador: {platform.processor()}")
        logger.info("================================")
    
    def cleanup(self):
        """Limpia todos los handlers y loggers."""
        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        
        self.loggers.clear()
        self.handlers_configured = False

# Instancia global del configurador
_logger_manager = SharaLogger()

def setup_logger(name: Optional[str] = None, **kwargs) -> logging.Logger:
    """
    Función de conveniencia para configurar un logger.
    
    Args:
        name: Nombre del logger
        **kwargs: Argumentos adicionales para configuración
        
    Returns:
        Logger configurado
    """
    return _logger_manager.setup_logger(name, **kwargs)

def get_logger(name: str) -> logging.Logger:
    """
    Función de conveniencia para obtener un logger.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger solicitado
    """
    return _logger_manager.get_logger(name)

def set_log_level(level: str, logger_name: Optional[str] = None):
    """
    Función de conveniencia para cambiar nivel de log.
    
    Args:
        level: Nuevo nivel
        logger_name: Nombre del logger específico
    """
    _logger_manager.set_level(level, logger_name)

def create_session_logger(session_id: str) -> logging.Logger:
    """
    Función de conveniencia para crear logger de sesión.
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        Logger de la sesión
    """
    return _logger_manager.create_session_logger(session_id)

def log_system_info(logger: Optional[logging.Logger] = None):
    """
    Función de conveniencia para registrar información del sistema.
    
    Args:
        logger: Logger a usar (se crea uno por defecto si no se proporciona)
    """
    if logger is None:
        logger = get_logger('system_info')
    
    _logger_manager.log_system_info(logger)

def cleanup_logging():
    """Función de conveniencia para limpiar el sistema de logging."""
    _logger_manager.cleanup()

# Configuración automática del logger principal al importar el módulo
try:
    main_logger = setup_logger()
    main_logger.debug("Sistema de logging inicializado correctamente")
except Exception as e:
    print(f"Error inicializando sistema de logging: {e}")