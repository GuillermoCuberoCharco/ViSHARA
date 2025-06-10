"""
Sistema de estilos y temas para SHARA Wizard
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from config import STYLE_COLORS

# Definición de colores del tema
class Colors:
    """Colores del tema principal."""
    PRIMARY = STYLE_COLORS['PRIMARY']          # #2c3e50
    SECONDARY = STYLE_COLORS['SECONDARY']      # #34495e
    SUCCESS = STYLE_COLORS['SUCCESS']          # #27ae60
    WARNING = STYLE_COLORS['WARNING']          # #f39c12
    ERROR = STYLE_COLORS['ERROR']              # #e74c3c
    INFO = STYLE_COLORS['INFO']                # #3498db
    BACKGROUND = STYLE_COLORS['BACKGROUND']    # #f8f9fa
    BORDER = STYLE_COLORS['BORDER']            # #dcdcdc
    
    # Colores adicionales
    WHITE = "#ffffff"
    BLACK = "#000000"
    LIGHT_GRAY = "#ecf0f1"
    DARK_GRAY = "#7f8c8d"
    TEXT_PRIMARY = "#2c3e50"
    TEXT_SECONDARY = "#7f8c8d"
    TEXT_MUTED = "#95a5a6"

# Estilos de componentes comunes
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: {Colors.SECONDARY};
        }}
        QPushButton:pressed {{
            background-color: #273746;
        }}
        QPushButton:disabled {{
            background-color: #bdc3c7;
            color: #7f8c8d;
        }}
    """,
    
    'success': f"""
        QPushButton {{
            background-color: {Colors.SUCCESS};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #229954;
        }}
        QPushButton:pressed {{
            background-color: #1e8449;
        }}
    """,
    
    'warning': f"""
        QPushButton {{
            background-color: {Colors.WARNING};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #e67e22;
        }}
        QPushButton:pressed {{
            background-color: #d35400;
        }}
    """,
    
    'error': f"""
        QPushButton {{
            background-color: {Colors.ERROR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #cb4335;
        }}
        QPushButton:pressed {{
            background-color: #b03a2e;
        }}
    """,
    
    'secondary': f"""
        QPushButton {{
            background-color: {Colors.LIGHT_GRAY};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #d5dbdb;
            border-color: #aab7b8;
        }}
        QPushButton:pressed {{
            background-color: #ccd1d1;
        }}
    """
}

INPUT_STYLES = {
    'default': f"""
        QLineEdit, QTextEdit {{
            background-color: {Colors.WHITE};
            border: 1px solid {Colors.BORDER};
            border-radius: 5px;
            padding: 8px;
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {Colors.INFO};
            outline: none;
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: {Colors.LIGHT_GRAY};
            color: {Colors.TEXT_MUTED};
        }}
    """,
    
    'error': f"""
        QLineEdit, QTextEdit {{
            background-color: #fdedec;
            border: 1px solid {Colors.ERROR};
            border-radius: 5px;
            padding: 8px;
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
        }}
    """,
    
    'success': f"""
        QLineEdit, QTextEdit {{
            background-color: #eafaf1;
            border: 1px solid {Colors.SUCCESS};
            border-radius: 5px;
            padding: 8px;
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
        }}
    """
}

FRAME_STYLES = {
    'default': f"""
        QFrame {{
            background-color: {Colors.WHITE};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 10px;
        }}
    """,
    
    'highlighted': f"""
        QFrame {{
            background-color: {Colors.WHITE};
            border: 2px solid {Colors.INFO};
            border-radius: 8px;
            padding: 10px;
        }}
    """,
    
    'panel': f"""
        QFrame {{
            background-color: {Colors.BACKGROUND};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 15px;
        }}
    """
}

LABEL_STYLES = {
    'heading': f"""
        QLabel {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
    """,
    
    'subheading': f"""
        QLabel {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
    """,
    
    'body': f"""
        QLabel {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            line-height: 1.4;
        }}
    """,
    
    'muted': f"""
        QLabel {{
            color: {Colors.TEXT_MUTED};
            font-size: 12px;
        }}
    """,
    
    'error': f"""
        QLabel {{
            color: {Colors.ERROR};
            font-size: 13px;
            font-weight: bold;
        }}
    """,
    
    'success': f"""
        QLabel {{
            color: {Colors.SUCCESS};
            font-size: 13px;
            font-weight: bold;
        }}
    """
}

# Estilo principal de la aplicación
MAIN_STYLE = f"""
/* Estilo principal de la aplicación */
QMainWindow {{
    background-color: {Colors.BACKGROUND};
    color: {Colors.TEXT_PRIMARY};
}}

/* Splitters */
QSplitter::handle {{
    background-color: {Colors.BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}
QSplitter::handle:hover {{
    background-color: {Colors.DARK_GRAY};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {Colors.LIGHT_GRAY};
    width: 12px;
    border-radius: 6px;
}}
QScrollBar::handle:vertical {{
    background-color: {Colors.DARK_GRAY};
    border-radius: 6px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {Colors.SECONDARY};
}}

QScrollBar:horizontal {{
    background-color: {Colors.LIGHT_GRAY};
    height: 12px;
    border-radius: 6px;
}}
QScrollBar::handle:horizontal {{
    background-color: {Colors.DARK_GRAY};
    border-radius: 6px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {Colors.SECONDARY};
}}

/* GroupBox */
QGroupBox {{
    font-weight: bold;
    border: 1px solid {Colors.BORDER};
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: {Colors.TEXT_PRIMARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}}

/* ComboBox */
QComboBox {{
    background-color: {Colors.WHITE};
    border: 1px solid {Colors.BORDER};
    border-radius: 5px;
    padding: 8px;
    min-width: 6em;
    color: {Colors.TEXT_PRIMARY};
}}
QComboBox:hover {{
    border-color: {Colors.INFO};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

/* ProgressBar */
QProgressBar {{
    background-color: {Colors.LIGHT_GRAY};
    border: 1px solid {Colors.BORDER};
    border-radius: 5px;
    text-align: center;
    color: {Colors.TEXT_PRIMARY};
}}
QProgressBar::chunk {{
    background-color: {Colors.INFO};
    border-radius: 5px;
}}

/* TabWidget */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    background-color: {Colors.WHITE};
}}
QTabBar::tab {{
    background-color: {Colors.LIGHT_GRAY};
    border: 1px solid {Colors.BORDER};
    padding: 8px 12px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {Colors.WHITE};
    border-bottom-color: {Colors.WHITE};
}}
QTabBar::tab:hover {{
    background-color: {Colors.BACKGROUND};
}}

/* ToolTip */
QToolTip {{
    background-color: {Colors.SECONDARY};
    color: {Colors.WHITE};
    border: 1px solid {Colors.PRIMARY};
    border-radius: 3px;
    padding: 5px;
    font-size: 12px;
}}

/* MenuBar y Menu */
QMenuBar {{
    background-color: {Colors.WHITE};
    border-bottom: 1px solid {Colors.BORDER};
    color: {Colors.TEXT_PRIMARY};
}}
QMenuBar::item {{
    background-color: transparent;
    padding: 8px 12px;
}}
QMenuBar::item:selected {{
    background-color: {Colors.LIGHT_GRAY};
}}

QMenu {{
    background-color: {Colors.WHITE};
    border: 1px solid {Colors.BORDER};
    color: {Colors.TEXT_PRIMARY};
}}
QMenu::item {{
    padding: 8px 12px;
}}
QMenu::item:selected {{
    background-color: {Colors.INFO};
    color: {Colors.WHITE};
}}
"""

def apply_main_window_styles(widget: QWidget):
    """
    Aplica los estilos principales a la ventana.
    
    Args:
        widget: Widget al que aplicar los estilos
    """
    widget.setStyleSheet(MAIN_STYLE)

def apply_button_style(button, style_type: str = 'primary'):
    """
    Aplica estilos a un botón.
    
    Args:
        button: Botón al que aplicar el estilo
        style_type: Tipo de estilo ('primary', 'success', 'warning', 'error', 'secondary')
    """
    if style_type in BUTTON_STYLES:
        button.setStyleSheet(BUTTON_STYLES[style_type])

def apply_input_style(input_widget, style_type: str = 'default'):
    """
    Aplica estilos a un campo de entrada.
    
    Args:
        input_widget: Widget de entrada al que aplicar el estilo
        style_type: Tipo de estilo ('default', 'error', 'success')
    """
    if style_type in INPUT_STYLES:
        input_widget.setStyleSheet(INPUT_STYLES[style_type])

def apply_frame_style(frame, style_type: str = 'default'):
    """
    Aplica estilos a un frame.
    
    Args:
        frame: Frame al que aplicar el estilo
        style_type: Tipo de estilo ('default', 'highlighted', 'panel')
    """
    if style_type in FRAME_STYLES:
        frame.setStyleSheet(FRAME_STYLES[style_type])

def apply_label_style(label, style_type: str = 'body'):
    """
    Aplica estilos a una etiqueta.
    
    Args:
        label: Etiqueta al que aplicar el estilo
        style_type: Tipo de estilo ('heading', 'subheading', 'body', 'muted', 'error', 'success')
    """
    if style_type in LABEL_STYLES:
        label.setStyleSheet(LABEL_STYLES[style_type])

def set_dark_theme(app: QApplication):
    """
    Configura un tema oscuro para la aplicación.
    
    Args:
        app: Aplicación Qt
    """
    dark_palette = QPalette()
    
    # Colores base
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    
    app.setPalette(dark_palette)

def create_status_style(status_type: str) -> str:
    """
    Crea un estilo para elementos de estado.
    
    Args:
        status_type: Tipo de estado ('success', 'warning', 'error', 'info')
        
    Returns:
        String con el estilo CSS
    """
    color_map = {
        'success': Colors.SUCCESS,
        'warning': Colors.WARNING,
        'error': Colors.ERROR,
        'info': Colors.INFO
    }
    
    color = color_map.get(status_type, Colors.INFO)
    
    return f"""
        background-color: {color}20;
        border: 1px solid {color};
        border-radius: 5px;
        padding: 8px;
        color: {color};
        font-weight: bold;
    """

def create_card_style(elevated: bool = False) -> str:
    """
    Crea un estilo de tarjeta.
    
    Args:
        elevated: Si la tarjeta debe tener sombra
        
    Returns:
        String con el estilo CSS
    """
    shadow = "box-shadow: 0 2px 4px rgba(0,0,0,0.1);" if elevated else ""
    
    return f"""
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.BORDER};
        border-radius: 8px;
        padding: 15px;
        {shadow}
    """

# Diccionario de temas disponibles
THEMES = {
    'light': {
        'name': 'Tema Claro',
        'primary': Colors.PRIMARY,
        'background': Colors.BACKGROUND,
        'text': Colors.TEXT_PRIMARY
    },
    'dark': {
        'name': 'Tema Oscuro', 
        'primary': '#1a1a1a',
        'background': '#2d2d2d',
        'text': '#ffffff'
    }
}

def get_theme_info(theme_name: str = 'light') -> dict:
    """
    Obtiene información de un tema.
    
    Args:
        theme_name: Nombre del tema
        
    Returns:
        Diccionario con información del tema
    """
    return THEMES.get(theme_name, THEMES['light'])

def apply_theme(app: QApplication, theme_name: str = 'light'):
    """
    Aplica un tema a la aplicación.
    
    Args:
        app: Aplicación Qt
        theme_name: Nombre del tema a aplicar
    """
    if theme_name == 'dark':
        set_dark_theme(app)
    else:
        # Tema claro (por defecto)
        app.setStyleSheet(MAIN_STYLE)