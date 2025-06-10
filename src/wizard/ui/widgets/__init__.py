"""
Paquete de widgets para SHARA Wizard
"""

from .chat_widget import ChatWidget
from .camera_widget import CameraWidget
from .web_widget import WebWidget
from .status_bar import StatusBar, StatusIndicator

__all__ = [
    'ChatWidget',
    'CameraWidget', 
    'WebWidget',
    'StatusBar',
    'StatusIndicator'
]