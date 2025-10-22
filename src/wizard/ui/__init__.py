"""
Paquete de interfaz de usuario para SHARA Wizard
"""

from .main_window import MainWindow
from .widgets import ChatWidget, CameraWidget, WebWidget, StatusBar
from .styles import apply_main_window_styles, apply_theme

__all__ = [
    'MainWindow',
    'ChatWidget',
    'CameraWidget', 
    'WebWidget',
    'StatusBar',
    'apply_main_window_styles',
    'apply_theme'
]