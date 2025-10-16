"""
Diálogo de respuesta para SHARA Wizard
"""

import base64
import asyncio
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QComboBox, QGroupBox, 
                            QButtonGroup, QScrollArea, QFrame, QWidget, QLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap

from config import RobotState
from utils.logger import get_logger
from ui.widgets.voice_recorder_widget import VoiceRecorderWidget

logger = get_logger(__name__)

STATE_EMOJIS= {
    RobotState.ATTENTION: "😮",
    RobotState.HELLO: "👋",
    RobotState.ANGRY: "😠",
    RobotState.SAD: "😢",
    RobotState.JOY: "😊",
    RobotState.YES: "👍",
    RobotState.NO: "🙅",
    RobotState.BLUSH: "😳"
}

STATE_DISPLAY_NAMES = {
    RobotState.ATTENTION: "Atención",
    RobotState.HELLO: "Saludo",
    RobotState.ANGRY: "Enfado",
    RobotState.SAD: "Tristeza",
    RobotState.JOY: "Alegría",
    RobotState.YES: "Afirmación",
    RobotState.NO: "Negación",
    RobotState.BLUSH: "Sonrojo"
}

# Mapeo de estados a imágenes y descripciones
STATE_CONFIG = {
    RobotState.ATTENTION: ("surprise.png", "Sorprendida"),
    RobotState.HELLO: ("neutral.png", "Saludando"), 
    RobotState.ANGRY: ("angry.png", "Enfadada"),
    RobotState.SAD: ("sad.png", "Triste"),
    RobotState.JOY: ("joy.png", "Feliz"),
    RobotState.YES: ("silly.png", "Asintiendo"),
    RobotState.NO: ("neutral.png", "Negativa"),
    RobotState.BLUSH: ("joy_blush.png", "Sonrojada")
}

class StateSelectionWidget(QFrame):
    """Widget para selección de estado emocional."""
    
    stateChanged = pyqtSignal(RobotState)
    
    def __init__(self, current_state: RobotState = RobotState.ATTENTION, 
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("Seleccione una emoción del robot")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Botones de estado en dos filas
        self._setup_state_buttons(layout, current_state)
    
    def _setup_state_buttons(self, parent_layout, current_state: RobotState):
        """Configura los botones de estado en dos filas."""
        self.button_group = QButtonGroup(self)
        self.state_buttons = {}
        
        # Primera fila de estados
        first_row_layout = QHBoxLayout()
        first_row_layout.setSpacing(5)
        first_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        first_row_states = [
            (RobotState.ATTENTION),
            (RobotState.HELLO),
            (RobotState.NO),
            (RobotState.YES)
        ]
        
        for state in first_row_states:
            button = self._create_state_button(state, current_state)
            first_row_layout.addWidget(button)
        
        parent_layout.addLayout(first_row_layout)
        
        # Segunda fila de estados
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(5)
        second_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        second_row_states = [
            (RobotState.ANGRY),
            (RobotState.SAD),
            (RobotState.JOY),
            (RobotState.BLUSH)
        ]
        
        for state in second_row_states:
            button = self._create_state_button(state, current_state)
            second_row_layout.addWidget(button)
        
        parent_layout.addLayout(second_row_layout)

    def _create_state_button(self, state: RobotState, current_state: RobotState) -> QPushButton:
        """Crea un botón para un estado específico."""
        emoji = STATE_EMOJIS.get(state, "❓")
        display_name = STATE_DISPLAY_NAMES.get(state, state.value)

        button = QPushButton(emoji)
        button.setCheckable(True)
        button.setFixedSize(80, 60)

        button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 2px solid #dcdcdc;
                border-radius: 8px;
                margin: 2px;
                font-size: 32px;
                color: #2c3e50;
            }
            QPushButton:checked {
                background-color: #2c3e50;
                border: 3px solid #3498db;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border: 2px solid #3498db;
                transform: scale(1.05);
            }
            QPushButton:checked:hover {
                background-color: #34495e;
                border: 3px solid #3498db;
            }
            QToolTip {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #3498db;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        button.setToolTip(f"🤖 {display_name}")
        
        if state == current_state:
            button.setChecked(True)
        
        button.clicked.connect(lambda checked, s=state: self._on_state_changed(s))
        self.button_group.addButton(button)
        self.state_buttons[state] = button
        
        return button
    
    def _on_state_changed(self, state: RobotState):
        """Maneja el cambio de estado."""
        self.stateChanged.emit(state)
    
    def get_selected_state(self) -> RobotState:
        """Obtiene el estado seleccionado."""
        for state, button in self.state_buttons.items():
            if button.isChecked():
                return state
        return RobotState.ATTENTION
    
    def set_selected_state(self, state: RobotState):
        """Establece el estado seleccionado."""
        if state in self.state_buttons:
            self.state_buttons[state].setChecked(True)


class StateVisualWidget(QFrame):
    """Widget para mostrar la imagen y descripción del estado actual."""
    
    def __init__(self, current_state: RobotState = RobotState.ATTENTION, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.current_state = current_state
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Imagen del estado
        self.state_image = QLabel()
        self.state_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_image.setMinimumSize(300, 300)
        self.state_image.setMaximumSize(400, 400)
        self.state_image.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.state_image)
        
        # Texto del estado
        self.state_text = QLabel()
        self.state_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_text.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.state_text.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 20px;
                padding: 10px 20px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.state_text)
        
        # Actualizar con el estado inicial
        self.update_state(current_state)
    
    def update_state(self, state: RobotState):
        """Actualiza la imagen y texto del estado."""
        self.current_state = state
        
        if state in STATE_CONFIG:
            image_name, description = STATE_CONFIG[state]
            
            # Actualizar imagen
            try:
                pixmap = QPixmap(f"resources/shara_faces/{image_name}")
                if pixmap.isNull():
                    # Imagen placeholder si no se encuentra el archivo
                    self.state_image.setText(f"Imagen:\n{image_name}")
                    self.state_image.setStyleSheet("""
                        QLabel {
                            border: 2px dashed #ccc;
                            border-radius: 10px;
                            background-color: #f8f9fa;
                            color: #6c757d;
                            font-size: 12px;
                        }
                    """)
                else:
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.state_image.setPixmap(scaled_pixmap)
                    self.state_image.setStyleSheet("""
                        QLabel {
                            border: 2px solid #ddd;
                            border-radius: 10px;
                            background-color: white;
                        }
                    """)
            except Exception as e:
                logger.warning(f"No se pudo cargar la imagen {image_name}: {e}")
                self.state_image.setText(f"Imagen:\n{image_name}")
            
            # Actualizar texto
            self.state_text.setText(f"Estoy: {description}")
        else:
            self.state_image.setText("Imagen no\ndisponible")
            self.state_text.setText(f"Estoy: {state.value}")


class ResponseBubbleWidget(QFrame):
    """Widget del bocadillo conversacional con respuesta del robot."""
    
    responseChanged = pyqtSignal()
    clearRequested = pyqtSignal()
    voiceRecordingRequested = pyqtSignal()
    
    def __init__(self, response: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container para el bocadillo con posicionamiento relativo
        self.bubble_container = QFrame()
        self.bubble_container.setStyleSheet("background-color: transparent;")
        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        
        # Editor de texto con estilo de bocadillo
        self.response_edit = QTextEdit()
        self.response_edit.setPlainText(response)
        self.response_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 3px solid #007bff;
                border-radius: 20px;
                padding: 15px;
                font-size: 16px;
                line-height: 1.4;
                min-height: 120px;
                color: #000000;
            }
            QTextEdit:focus {
                border-color: #0056b3;
            }
        """)
        bubble_layout.addWidget(self.response_edit)
        
        layout.addWidget(self.bubble_container)
        
        # Crear botones superpuestos
        self._create_overlay_buttons()
        
        # Conectar señales
        self.response_edit.textChanged.connect(self.responseChanged.emit)
    
    def _create_overlay_buttons(self):
        """Crea los botones superpuestos en el bocadillo."""
        # Botón de papelera (esquina superior derecha)
        self.clear_button = QPushButton("🗑️")
        self.clear_button.setParent(self.bubble_container)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 10px;
                padding: 2px;
                min-width: 16px;
                min-height: 16px;
                max-width: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.clear_button.clicked.connect(self.clearRequested.emit)
        self.clear_button.setToolTip("Limpiar respuesta")
        
        # Botón de micrófono (esquina inferior derecha)
        self.voice_button = QPushButton("🎤")
        self.voice_button.setParent(self.bubble_container)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 10px;
                padding: 2px;
                min-width: 16px;
                min-height: 16px;
                max-width: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.voice_button.clicked.connect(self.voiceRecordingRequested.emit)
        self.voice_button.setToolTip("Grabar respuesta de voz")
        
        # Estado de grabación
        self.is_recording = False
    
    def resizeEvent(self, event):
        """Reposiciona los botones cuando cambia el tamaño."""
        super().resizeEvent(event)
        self._position_overlay_buttons()
    
    def _position_overlay_buttons(self):
        """Posiciona los botones superpuestos."""
        if hasattr(self, 'clear_button') and hasattr(self, 'voice_button'):
            # Posición del botón de papelera (esquina superior derecha)
            self.clear_button.move(
                self.bubble_container.width() - self.clear_button.width() - 5,
                5
            )
            
            # Posición del botón de micrófono (esquina inferior derecha)
            self.voice_button.move(
                self.bubble_container.width() - self.voice_button.width() - 5,
                self.bubble_container.height() - self.voice_button.height() - 5
            )
    
    def set_recording_state(self, is_recording: bool):
        """Actualiza el estado visual del botón de grabación."""
        if hasattr(self, 'voice_button'):
            if is_recording:
                self.voice_button.setText("⏹️")  # Icono de parar
                self.voice_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f96300;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 10px;
                        padding: 2px;
                        min-width: 16px;
                        min-height: 16px;
                        max-width: 30px;
                        max-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                self.voice_button.setToolTip("Clic para enviar grabación")
            else:
                self.voice_button.setText("🎤")
                self.voice_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 10px;
                        padding: 2px;
                        min-width: 16px;
                        min-height: 16px;
                        max-width: 30px;
                        max-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                    QPushButton:pressed {
                        background-color: #1e7e34;
                    }
                """)
                self.voice_button.setToolTip("Grabar respuesta de voz")
            self.is_recording = is_recording
    
    def get_response(self) -> str:
        """Obtiene el texto de la respuesta."""
        return self.response_edit.toPlainText().strip()
    
    def set_response(self, response: str):
        """Establece el texto de la respuesta."""
        self.response_edit.setPlainText(response)
    
    def clear_response(self):
        """Limpia el texto de la respuesta."""
        self.response_edit.clear()
    
    def focus_editor(self):
        """Pone el foco en el editor."""
        self.response_edit.setFocus()

    def sync_recording_state(self, is_recording: bool):
        """Sincroniza el estado de grabación con el botón."""
        if hasattr(self, 'voice_button'):
            if is_recording:
                self.voice_button.setText("⏹️")
                self.voice_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f96300;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 10px;
                        padding: 2px;
                        min-width: 16px;
                        min-height: 16px;
                        max-width: 30px;
                        max-height: 30px;
                    }
                    QPushButton:hover { background-color: #c82333; }
                """)
                self.voice_button.setToolTip("Clic para detener grabación")
            else:
                self.voice_button.setText("🎤")
                self.voice_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 10px;
                        padding: 2px;
                        min-width: 16px;
                        min-height: 16px;
                        max-width: 16px;
                        max-height: 16px;
                    }
                    QPushButton:hover { background-color: #218838; }
                    QPushButton:pressed { background-color: #1e7e34; }
                """)
                self.voice_button.setToolTip("Grabar respuesta de voz")


class ClickableResponseButton(QFrame):
    """Widget personalizado que actúa como un botón con word wrap."""
    
    clicked = pyqtSignal()
    
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout para el label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Label con word wrap
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.label)
        
        # Estilo del frame (botón)
        self._set_normal_style()
    
    def _set_normal_style(self):
        """Aplica el estilo normal."""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #007bff;
                border-radius: 8px;
            }
        """)
    
    def _set_hover_style(self):
        """Aplica el estilo de hover."""
        self.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border: 2px solid #0056b3;
                border-radius: 8px;
            }
        """)
    
    def _set_pressed_style(self):
        """Aplica el estilo de pressed."""
        self.setStyleSheet("""
            QFrame {
                background-color: #cce5ff;
                border: 2px solid #0056b3;
                border-radius: 8px;
            }
        """)
    
    def enterEvent(self, event):
        """Evento al entrar con el mouse."""
        self._set_hover_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Evento al salir con el mouse."""
        self._set_normal_style()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Evento al presionar el mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_pressed_style()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Evento al soltar el mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_hover_style()
            self.clicked.emit()
        super().mouseReleaseEvent(event)

class AIResponseSelector(QFrame):
    """Widget para seleccionar respuestas generadas por OpenAI."""
    
    responseSelected = pyqtSignal(str)
    
    def __init__(self, current_state: RobotState = RobotState.ATTENTION, 
                 ai_responses: Dict[str, Dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.current_state = current_state
        self.ai_responses = ai_responses or {}
        self.response_buttons = []
        
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)

        # Título
        title = QLabel("Respuestas Alternativas de Shara")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        self.main_layout.addWidget(title)

        # Contenedor de botones con scroll
        self.buttons_scroll = QScrollArea()
        self.buttons_scroll.setWidgetResizable(True)
        self.buttons_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Widget contendor de botones
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setSpacing(5)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.buttons_scroll.setWidget(self.buttons_container)
        self.main_layout.addWidget(self.buttons_scroll)

        # Actualizar respuestas para el estado actual
        self.update_responses(current_state)
    
    def update_responses(self, state):
        """Actualiza las respuestas disponibles para un estado."""
        # Validar y normalizar el parámetro state
        if isinstance(state, str):
            try:
                state = RobotState(state)
            except ValueError:
                logger.warning(f"Estado inválido en update_responses: {state}, usando ATTENTION por defecto")
                state = RobotState.ATTENTION
        elif not isinstance(state, RobotState):
            logger.warning(f"Tipo de estado no válido en update_responses: {type(state)}, usando ATTENTION por defecto")
            state = RobotState.ATTENTION

        self.current_state = state

        self._clear_buttons()
        
        # Validar que ai_responses sea un diccionario
        if not isinstance(self.ai_responses, dict):
            logger.warning(f"ai_responses no es un diccionario: {type(self.ai_responses)}")
            return

        # Agregar respuestas para el estado actual
        state_key = state.value
        responses_found = False

        if state_key in self.ai_responses:
            response_data = self.ai_responses[state_key]

            if isinstance(response_data, dict):
                response_text = response_data.get('text', '')
                if response_text:
                    self._create_response_button(response_text, state_key, 1)
                    responses_found = True
            
            elif isinstance(response_data, list):
                for idx, resp in enumerate(response_data, 1):
                    if isinstance(resp, dict):
                        response_text = resp.get('text', '')
                        if response_text:
                            self._create_response_button(response_text, state_key, idx)
                            responses_found = True
        
        # Si no hay respuestas, mostrar mensaje informativo
        if not responses_found:
            self._show_no_responses_message()
    
    def set_ai_responses(self, ai_responses: Dict[str, Dict]):
        """Establece las respuestas generadas por IA."""
        self.ai_responses = ai_responses or {}
        self.update_responses(self.current_state)

    def _clear_buttons(self):
        """Limpia los botones existentes."""
        for btn in self.response_buttons:
            btn.deleteLater()
        self.response_buttons.clear()

    def _create_response_button(self, response_text: str, state_key: str, index: int):
        """Crea un botón para una respuesta específica."""
     
       # Crear botón clickeable con texto completo
        button = ClickableResponseButton(f"{response_text}")

        # Conectar señal - usar lambda para capturar el texto completo
        button.clicked.connect(lambda text=response_text: self._on_button_clicked(text))
        
        # Agregar al layout y a la lista
        self.buttons_layout.addWidget(button)
        self.response_buttons.append(button)
        
        logger.debug(f"Botón creado para respuesta {index} del estado {state_key}")

    def _show_no_responses_message(self):
        """Muestra un mensaje cuando no hay respuestas disponibles."""
        label = QLabel("No hay respuestas disponibles para este estado")
        label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-style: italic;
                font-size: 12px;
                padding: 10px;
            }
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttons_layout.addWidget(label)
        self.response_buttons.append(label)
    
    def _on_button_clicked(self, response_text: str):
        """Maneja el clic en un botón de respuesta."""
        logger.debug(f"Respuesta seleccionada: {response_text[:50]}...")
        self.responseSelected.emit(response_text)
    
    def set_ai_responses(self, ai_responses: Dict[str, Dict]):
        """Establece las respuestas generadas por IA."""
        self.ai_responses = ai_responses or {}
        self.update_responses(self.current_state)

    
    def _on_response_selected(self, text: str):
        """Maneja la selección de respuesta."""
        if text and not text.startswith("--") and not text.startswith("No hay"):
            # Obtener el texto completo asociado al índice seleccionado
            current_index = self.response_combo.currentIndex()
            full_response = self.response_combo.itemData(current_index)
            if full_response:
                self.responseSelected.emit(full_response)


class ResponseDialog(QDialog):
    """
    Diálogo para editar y validar respuestas del robot antes de enviarlas.
    Nueva versión con diseño de bocadillo conversacional.
    """
    
    finished = pyqtSignal(bool, str, str)  # accepted, response, state
    
    def __init__(self, response: str, current_state: RobotState = RobotState.ATTENTION, 
                 ai_responses: dict = None, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
                
        # Validar y normalizar current_state
        if isinstance(current_state, str):
            try:
                current_state = RobotState(current_state)
            except ValueError:
                logger.warning(f"Estado inválido en ResponseDialog: {current_state}, usando ATTENTION por defecto")
                current_state = RobotState.ATTENTION
        elif isinstance(current_state, dict):
            logger.warning(f"Se recibió un diccionario como estado en ResponseDialog: {current_state}, usando ATTENTION por defecto")
            current_state = RobotState.ATTENTION
        elif not isinstance(current_state, RobotState):
            logger.warning(f"Tipo de estado no válido en ResponseDialog: {type(current_state)}, usando ATTENTION por defecto")
            current_state = RobotState.ATTENTION
        
        self.response = response
        self.current_state = current_state
        self.ai_responses = ai_responses or {}
        
        # Variables para grabación de voz
        self.is_recording = False
        self.audio_data = None
        self.voice_widget = None
        self.voice_recorder = None
        
        # Componentes
        self.state_widget = None
        self.visual_widget = None
        self.bubble_widget = None
        self.selector_widget = None
        
        self._setup_ui()
        self._connect_signals()
        
        logger.debug(f"ResponseDialog creado para estado: {current_state.value}")
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle('Respuesta del Robot')
        self.setMinimumWidth(800)
        # self.setMinimumHeight(800)
        self.setModal(True)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
    
        left_column = QVBoxLayout()
        left_column.setSpacing(15)
        
        # Selector de estados emocionales (ahora en columna izquierda)
        self.state_widget = StateSelectionWidget(self.current_state)
        left_column.addWidget(self.state_widget)
        
        # Imagen y estado visual
        self.visual_widget = StateVisualWidget(self.current_state)
        left_column.addWidget(self.visual_widget)
        
        # Agregar stretch al final para que los widgets se mantengan arriba
        left_column.addStretch()
        
        # Crear widget container para la columna izquierda
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        content_layout.addWidget(left_widget, 1)

        right_column = QVBoxLayout()
        right_column.setSpacing(15)
        
        # Bocadillo conversacional
        self.bubble_widget = ResponseBubbleWidget(self.response)
        right_column.addWidget(self.bubble_widget)
        
        # Selector de respuestas de IA
        self.selector_widget = AIResponseSelector(self.current_state, self.ai_responses)
        right_column.addWidget(self.selector_widget, 0)
        
        # Botones de acción
        self._setup_action_buttons(right_column)
        
        # Crear widget container para la columna derecha
        right_widget = QWidget()
        right_widget.setLayout(right_column)
        content_layout.addWidget(right_widget, 1)  # 50%
        
        # Agregar el layout de dos columnas al layout principal
        main_layout.addLayout(content_layout)
        
        # Ajustar tamaño después de construir toda la UI
        QTimer.singleShot(100, self._adjust_dialog_size)
    
    def _get_voice_recorder(self):
        """Obtiene o crea el widget de grabación de voz."""
        if self.voice_recorder is None:
            self.voice_recorder = VoiceRecorderWidget()
            self.voice_recorder.hide()
            self.voice_recorder.recording_finished.connect(self._on_voice_recording_finished)
        return self.voice_recorder

    def _adjust_dialog_size(self):
        """Ajusta el tamaño del diálogo para mostrar todo el contenido."""
        self.adjustSize()
        
        # Asegurar un tamaño mínimo razonable
        current_height = self.height()
        if current_height < 600:
            self.resize(self.width(), 600)
        
        # Limitar tamaño máximo para no ocupar toda la pantalla
        screen = self.screen().availableGeometry()
        max_height = int(screen.height() * 0.9)
        
        if self.height() > max_height:
            self.resize(self.width(), max_height)

    def _setup_action_buttons(self, parent_layout):
        """Configura los botones de acción."""
        buttons_layout = QHBoxLayout()
        
        # Botón cancelar
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # Botón enviar
        send_button = QPushButton("Enviar")
        send_button.clicked.connect(self.accept)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(send_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def _connect_signals(self):
        """Conecta las señales entre componentes."""
        # Conexión del widget de estado
        if self.state_widget:
            self.state_widget.stateChanged.connect(self._on_state_changed)
        
        # Conexión del selector de respuestas de IA
        if self.selector_widget:
            self.selector_widget.responseSelected.connect(self._on_ai_response_selected)
        
        # Conexión del widget de bocadillo
        if self.bubble_widget:
            self.bubble_widget.clearRequested.connect(self._on_clear_requested)
            self.bubble_widget.voiceRecordingRequested.connect(self._on_voice_recording_requested)

        # Conexión de grabación de voz
        pass
    
    def _on_state_changed(self, new_state: RobotState):
        """Maneja el cambio de estado emocional."""
        logger.debug(f"Estado cambiado a: {new_state.value}")
        self.current_state = new_state
        
        # Actualizar imagen y descripción
        if self.visual_widget:
            self.visual_widget.update_state(new_state)
        
        # Actualizar selector de respuestas
        if self.selector_widget:
            self.selector_widget.update_responses(new_state)
    
    def _on_ai_response_selected(self, response: str):
        """Maneja la selección de respuesta de IA."""
        if self.bubble_widget:
            self.bubble_widget.set_response(response)
            self.bubble_widget.focus_editor()
        logger.debug(f"Respuesta de IA seleccionada: {response[:50]}...")
    
    def _on_clear_requested(self):
        """Maneja la solicitud de limpiar respuesta."""
        if self.bubble_widget:
            self.bubble_widget.clear_response()
        logger.debug("Respuesta limpiada")
    
    def _on_voice_recording_requested(self):
        """Maneja la solicitud de grabación de voz como toggle directo."""
        voice_recorder = self._get_voice_recorder()
        voice_recorder._toggle_recording()

        if self.bubble_widget:
            # Sincronizar estado de grabación con el botón
            is_recording = self.voice_recorder.is_recording
            self.bubble_widget.sync_recording_state(is_recording)
    
    def _start_voice_recording(self):
        """Inicia la grabación de voz."""
        try:
            # Crear widget de grabación si no existe
            if not self.voice_widget:
                self.voice_widget = VoiceRecorderWidget()
                self.voice_widget.recording_finished.connect(self._on_voice_recording_finished)
                # Ocultar la ventana del widget de grabación
                self.voice_widget.hide()
            
            # Iniciar grabación programáticamente
            if hasattr(self.voice_widget, 'start_recording'):
                self.voice_widget.start_recording()
            
            # Actualizar estado visual
            self.is_recording = True
            if self.bubble_widget:
                self.bubble_widget.set_recording_state(True)
            
            logger.debug("Grabación de voz iniciada")
            
        except Exception as e:
            logger.error(f"Error al iniciar grabación de voz: {e}")
            self.is_recording = False
            if self.bubble_widget:
                self.bubble_widget.set_recording_state(False)
    
    def _stop_voice_recording(self):
        """Detiene la grabación de voz y procesa el resultado."""
        try:
            if self.voice_widget and hasattr(self.voice_widget, 'stop_recording'):
                self.voice_widget.stop_recording()
            
            # Actualizar estado visual
            self.is_recording = False
            if self.bubble_widget:
                self.bubble_widget.set_recording_state(False)
            
            logger.debug("Grabación de voz detenida")
            
        except Exception as e:
            logger.error(f"Error al detener grabación de voz: {e}")
            self.is_recording = False
            if self.bubble_widget:
                self.bubble_widget.set_recording_state(False)

    def _on_voice_recording_finished(self, audio_data: bytes):
        """Maneja la finalización de la grabación de voz y envía directamente."""
        try:
            # Actualizar estado visual
            self.is_recording = False
            if self.bubble_widget:
                self.bubble_widget.sync_recording_state(False)
            
            # Obtener socket service desde la aplicación principal
            app = self.parent()
            while app and app.parent():
                app = app.parent()

            if app and hasattr(app, 'get_service'):
                socket_service = app.get_service('socket')
                if socket_service:
                    # Enviar datos de audio al servicio
                    robot_state = self.get_state().value
                    asyncio.create_task(
                        self._send_voice(socket_service, audio_data, robot_state)
                    )
                else:
                    logger.error("Socket service no disponible")
            else:
                logger.error("No se pudo obtener el socket service")
        
        except Exception as e:
            logger.error(f"Error al procesar grabación de voz: {e}")
            # Resetear estado en caso de error
            self.is_recording = False
            if self.bubble_widget:
                self.bubble_widget.set_recording_state(False)

    async def _send_voice(self, socket_service, audio_data: bytes, robot_state: str):
        """Envía los datos de voz directamente al servicio de socket."""
        try:
            # Enviar mensaje al servicio
            logger.debug("Estado del robot: %s", robot_state)
            success = await socket_service.send_voice_response(audio_data, robot_state)

            if success:
                logger.info("Datos de voz enviados correctamente")
                self.finished.emit(False, '', '')
                super().accept()
            else:
                logger.error("Error al enviar datos de voz: servicio no disponible")

        except Exception as e:
            logger.error(f"Error al enviar datos de voz: {e}")
    
    def get_response(self) -> str:
        """Obtiene la respuesta editada."""
        return self.bubble_widget.get_response() if self.bubble_widget else ""
    
    def get_state(self) -> RobotState:
        """Obtiene el estado seleccionado."""
        return self.state_widget.get_selected_state() if self.state_widget else self.current_state
    
    def accept(self):
        """Maneja la aceptación del diálogo."""
        response = self.get_response()
        state = self.get_state()
        
        if not response:
            # Mostrar advertencia si no hay respuesta
            if self.bubble_widget:
                self.bubble_widget.response_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #fff3cd;
                        border: 3px solid #ffeaa7;
                        border-radius: 20px;
                        padding: 15px;
                        font-size: 13px;
                        line-height: 1.4;
                        min-height: 120px;
                        color: #000000;
                    }
                """)
            return
        
        # Emitir señal con los datos
        self.finished.emit(True, response, state.value)
        
        logger.info(f"Respuesta aceptada: {response[:50]}... (Estado: {state.value})")
        super().accept()
    
    def reject(self):
        """Maneja la cancelación del diálogo."""
        # Detener grabación si está activa
        if self.is_recording:
            self._stop_voice_recording()
        
        self.finished.emit(False, '', '')
        logger.debug("Respuesta cancelada")
        super().reject()
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        # Detener grabación si está activa
        if self.is_recording:
            self._stop_voice_recording()
        
        # Limpiar widget de voz
        if self.voice_widget:
            try:
                self.voice_widget.close()
                self.voice_widget = None
            except:
                pass

        # Limpiar grabador de voz
        if self.voice_recorder is not None:
            try:
                self.voice_recorder.cleanup()
            except:
                pass
        
        self.finished.emit(False, '', '')
        event.accept()
        super().closeEvent(event)
    
    def set_response(self, response: str):
        """
        Establece la respuesta en el editor.
        
        Args:
            response: Nueva respuesta
        """
        if self.bubble_widget:
            self.bubble_widget.set_response(response)
    
    def set_state(self, state: RobotState):
        """
        Establece el estado seleccionado.
        
        Args:
            state: Nuevo estado
        """
        if isinstance(state, str):
            try:
                state = RobotState(state)
            except ValueError:
                state = RobotState.ATTENTION
        elif isinstance(state, dict):
            state = RobotState.ATTENTION
        elif not isinstance(state, RobotState):
            state = RobotState.ATTENTION

        self.current_state = state
        if self.state_widget:
            self.state_widget.set_selected_state(state)
        if self.visual_widget:
            self.visual_widget.update_state(state)
        if self.selector_widget:
            self.selector_widget.update_responses(state)
    
    def focus_response_editor(self):
        """Pone el foco en el editor de respuesta."""
        if self.bubble_widget:
            self.bubble_widget.focus_editor()