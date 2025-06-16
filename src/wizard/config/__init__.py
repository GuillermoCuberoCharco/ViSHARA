"""
Paquete de configuración para SHARA Wizard
"""

from .settings import settings, AppSettings
from .constants import (
    RobotState,
    MessageType,
    ConnectionState,
    OperationMode,
    SystemEvent,
    PRESET_RESPONSES,
    WINDOW_GEOMETRY,
    SPLITTER_RATIOS,
    VIDEO_CONFIG,
    CHAT_CONFIG,
    TIMEOUTS,
    STYLE_COLORS
)

__all__ = [
    'settings',
    'AppSettings',
    'RobotState',
    'MessageType',
    'ConnectionState',
    'OperationMode',
    'SystemEvent',
    'PRESET_RESPONSES',
    'WINDOW_GEOMETRY',
    'SPLITTER_RATIOS',
    'VIDEO_CONFIG',
    'CHAT_CONFIG',
    'TIMEOUTS',
    'STYLE_COLORS'
]