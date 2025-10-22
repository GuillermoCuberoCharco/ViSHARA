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
        
        # Conectar señales
        self.response_edit.textChanged.connect(self.responseChanged.emit)
    
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

class ResponseActionsWidget(QFrame):
    """Widget con botones de acción para la respuesta (borrado y grabación de voz)."""

    clearRequested = pyqtSignal()
    voiceRecordingRequested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.is_recording = False

        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Botón de borrar respuesta
        self.clear_button = QPushButton("🗑️")
        self.clear_button.setFixedSize(30, 17)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 25px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 100px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #c82333;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)

        self.clear_button.clicked.connect(self.clearRequested.emit)
        self.clear_button.setToolTip("Borrar respuesta")

        layout.addWidget(self.clear_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Botón de grabación de voz
        self.voice_button = QPushButton("🎙️")
        self.voice_button.setFixedSize(30, 17)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 25px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 120px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        self.voice_button.clicked.connect(self.voiceRecordingRequested.emit)
        self.voice_button.setToolTip("Grabar respuesta por voz")
        layout.addWidget(self.voice_button, 0, Qt.AlignmentFlag.AlignCenter)

        

    def sync_recording_state(self, is_recording: bool):
        """Sincroniza el estado del botón de grabación."""
        self.is_recording = is_recording
        if is_recording:
            self.voice_button.setText("⏹️")
            self.clear_button.setFixedSize(30, 17)
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: #f96300;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 25px;
                    font-weight: bold;
                    padding: 8px 16px;
                    min-width: 120px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.voice_button.setToolTip("Detener grabación de voz")
        else:
            self.voice_button.setText("🎙️")
            self.clear_button.setFixedSize(30, 17)
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 25px;
                    font-weight: bold;
                    padding: 8px 16px;
                    min-width: 120px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
            self.voice_button.setToolTip("Grabar respuesta por voz")

class AIResponseSelector(QFrame):
    """Widget para seleccionar respuestas generadas por OpenAI usando un ComboBox."""
    
    responseSelected = pyqtSignal(str)
    
    def __init__(self, current_state: RobotState = RobotState.ATTENTION, 
                 ai_responses: Dict[str, Dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.current_state = current_state
        self.ai_responses = ai_responses or {}
        
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # ComboBox para respuestas
        self.response_combo = QComboBox()
        self.response_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 2px solid #007bff;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                min-height: 30px;
            }
            QComboBox:hover {
                border-color: #0056b3;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #007bff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #007bff;
                selection-background-color: #e7f3ff;
                selection-color: #000000;
                padding: 5px;
                color: #2c3e50;
            }
        """)
        
        # Conectar señal de selección
        self.response_combo.activated.connect(self._on_response_selected)
        
        self.main_layout.addWidget(self.response_combo)
        
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

        self.response_combo.blockSignals(True)

        self.response_combo.clear()

        self.response_combo.setPlaceholderText("🤖 Respuestas Alternativas de Shara")
        self.response_combo.setCurrentIndex(-1)
        
        # Validar que ai_responses sea un diccionario
        if not isinstance(self.ai_responses, dict):
            logger.warning(f"ai_responses no es un diccionario: {type(self.ai_responses)}")
            self.response_combo.addItem("-- No hay respuestas disponibles --")
            return

        # Agregar respuestas para el estado actual
        state_key = state.value
        responses_found = False

        if state_key in self.ai_responses:
            response_data = self.ai_responses[state_key]

            if isinstance(response_data, dict):
                response_text = response_data.get('text', '')
                if response_text:
                    # Truncar para mostrar en el combo, pero guardar texto completo
                    display_text = response_text[:80] + "..." if len(response_text) > 80 else response_text
                    self.response_combo.addItem(display_text)
                    self.response_combo.setItemData(0, response_text)
                    responses_found = True
            
            elif isinstance(response_data, list):
                for idx, resp in enumerate(response_data):
                    if isinstance(resp, dict):
                        response_text = resp.get('text', '')
                        if response_text:
                            # Truncar para mostrar en el combo, pero guardar texto completo
                            display_text = f"{idx + 1}. {response_text[:70]}..." if len(response_text) > 70 else f"{idx + 1}. {response_text}"
                            self.response_combo.addItem(display_text)
                            self.response_combo.setItemData(idx, response_text)
                            responses_found = True
        
        # Si no hay respuestas, mostrar mensaje
        if not responses_found:
            self.response_combo.addItem("-- No hay respuestas para este estado --")
            self.response_combo.setItemData(1, None)

        self.response_combo.setCurrentIndex(-1)
        self.response_combo.blockSignals(False)
        
        logger.debug(f"ComboBox actualizado con respuestas para estado: {state_key}")
    
    def _on_response_selected(self, index: int):
        """Maneja la selección de respuesta."""
        if index < 0: 
            return

        full_response = self.response_combo.itemData(index)
        
        if full_response:
            self.responseSelected.emit(full_response)
            logger.debug(f"Respuesta seleccionada del combo: {full_response[:50]}...")
            
            # Volver al placeholder después de seleccionar
            self.response_combo.blockSignals(True)
            self.response_combo.setCurrentIndex(-1)
            self.response_combo.blockSignals(False)
    
    def set_ai_responses(self, ai_responses: Dict[str, Dict]):
        """Establece las respuestas generadas por IA."""
        self.ai_responses = ai_responses or {}
        self.update_responses(self.current_state)

    def clear_responses(self):
        """Limpia las respuestas mostradas."""
        self.response_combo.blockSignals(True)
        self.response_combo.clear()
        self.response_combo.setPlaceholderText("🤖 Respuestas Alternativas de Shara")
        self.response_combo.setCurrentIndex(-1)
        self.response_combo.blockSignals(False)
        self.ai_responses = {}
        logger.debug("ComboBox de respuestas limpiado")
