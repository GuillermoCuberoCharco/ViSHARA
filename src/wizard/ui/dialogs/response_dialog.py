"""
Diálogo de respuesta para SHARA Wizard
"""

import base64
import asyncio
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QComboBox, QGroupBox, 
                            QButtonGroup, QScrollArea, QFrame, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import RobotState
from utils.logger import get_logger
from ui.widgets.voice_recorder_widget import VoiceRecorderWidget

logger = get_logger(__name__)

class StateSelectionWidget(QFrame):
    """Widget para selección de estado emocional."""
    
    stateChanged = pyqtSignal(RobotState)
    
    def __init__(self, current_state: RobotState = RobotState.ATTENTION, 
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("Estado Emocional del Robot")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Botones de estado
        self._setup_state_buttons(layout, current_state)
    
    def _setup_state_buttons(self, parent_layout, current_state: RobotState):
        """Configura los botones de estado."""
        # Contenedor de botones
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(5)
        
        # Grupo de botones exclusivos
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Crear botones para cada estado
        self.state_buttons = {}
        for state in RobotState:
            button = QPushButton(state.value)
            button.setCheckable(True)
            button.setFixedSize(80, 50)
            
            # Aplicar estilos
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    color: #495057;
                    font-size: 9px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #007bff;
                    color: white;
                    border-color: #0056b3;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:checked:hover {
                    background-color: #0056b3;
                }
            """)
            
            # Conectar señal
            button.clicked.connect(lambda checked, s=state: self._on_state_selected(s))
            
            # Agregar al layout y grupo
            buttons_layout.addWidget(button)
            self.button_group.addButton(button)
            self.state_buttons[state] = button
        
        # Establecer estado inicial
        if current_state in self.state_buttons:
            self.state_buttons[current_state].setChecked(True)
        
        parent_layout.addWidget(buttons_frame)
    
    def _on_state_selected(self, state: RobotState):
        """Maneja la selección de estado."""
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

class PresetResponseWidget(QFrame):
    """Widget para respuestas predefinidas."""
    
    responseSelected = pyqtSignal(str)
    
    def __init__(self, current_state: RobotState = RobotState.ATTENTION,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.current_state = current_state
        
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("Respuestas Predefinidas")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # ComboBox para respuestas
        self.response_combo = QComboBox()
        self.response_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)
        
        self.response_combo.currentTextChanged.connect(self._on_response_selected)
        layout.addWidget(self.response_combo)
        
        # Actualizar respuestas para el estado actual
        self.update_responses(current_state)
    
    def update_responses(self, state: RobotState):
        """Actualiza las respuestas disponibles para un estado."""
        self.current_state = state
        self.response_combo.clear()
        
        # Agregar opción por defecto
        self.response_combo.addItem("-- Selecciona una respuesta predefinida --")
        
    
    def _on_response_selected(self, text: str):
        """Maneja la selección de respuesta."""
        if text and text != "-- Selecciona una respuesta predefinida --":
            self.responseSelected.emit(text)

class ResponseDialog(QDialog):
    """
    Diálogo para editar y validar respuestas del robot antes de enviarlas.
    """
    
    finished = pyqtSignal(bool, str, str)  # accepted, response, state
    
    def __init__(self, response: str, current_state: RobotState = RobotState.ATTENTION, ai_responses: dict[str, dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.response = response
        self.current_state = current_state
        self.ai_responses = ai_responses or {}
        
        # Componentes
        self.response_edit = None
        self.state_widget = None
        self.ai_widget = None
        
        self._setup_ui()
        self._connect_signals()
        
        logger.debug(f"ResponseDialog creado para estado: {current_state.value}")
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle('Respuesta del Robot')
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setModal(False)  # Diálogo no modal
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Sección de respuesta actual
        self._setup_response_section(layout)
        
        # Sección de estado emocional
        self.state_widget = StateSelectionWidget(self.current_state)
        layout.addWidget(self.state_widget)
        
        # Sección de respuestas predefinidas
        self.ai_widget = AIResponseWidget(self.current_state, self.ai_responses)
        layout.addWidget(self.ai_widget)

        # Sección de respuesta por voz
        voice_group = QGroupBox("Respuesta por Voz")
        voice_layout = QVBoxLayout(voice_group)

        # Etiqueta informativa
        voice_info = QLabel("Graba tu respuesta. Se transcribirá y enviará automáticamente.")
        voice_info.setStyleSheet("color: #6c757d; font-style: italic; margin-bottom: 5px;")
        voice_layout.addWidget(voice_info)

        # Widget de grabación de voz
        self.voice_recorder = VoiceRecorderWidget(self)
        voice_layout.addWidget(self.voice_recorder)
        layout.addWidget(voice_group)
        
        # Botones de acción
        self._setup_action_buttons(layout)
        
        # Aplicar estilos globales
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
    
    def _setup_response_section(self, parent_layout):
        """Configura la sección de edición de respuesta."""
        response_group = QGroupBox("Respuesta Actual")
        response_layout = QVBoxLayout(response_group)
        
        # Etiqueta informativa
        info_label = QLabel(f"[Emoción detectada: {self.current_state.value}]")
        info_label.setStyleSheet("color: #6c757d; font-style: italic; margin-bottom: 5px;")
        response_layout.addWidget(info_label)
        
        # Editor de texto
        self.response_edit = QTextEdit(self.response)
        self.response_edit.setMinimumHeight(120)
        self.response_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #007bff;
            }
        """)
        response_layout.addWidget(self.response_edit)
        
        parent_layout.addWidget(response_group)
    
    def _setup_action_buttons(self, parent_layout):
        """Configura los botones de acción."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Botón de envío
        send_button = QPushButton('Enviar Respuesta')
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        send_button.clicked.connect(self.accept)
        button_layout.addWidget(send_button)
        
        # Botón de cancelación
        cancel_button = QPushButton('Cancelar')
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Botón de limpiar
        clear_button = QPushButton('Limpiar')
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        clear_button.clicked.connect(self._clear_response)
        button_layout.addWidget(clear_button)
        
        parent_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Conecta las señales de los widgets."""
        # Actualizar respuestas predefinidas cuando cambie el estado
        self.state_widget.stateChanged.connect(self.ai_widget.update_responses)
        
        # Insertar respuesta predefinida en el editor
        self.ai_widget.responseSelected.connect(self._insert_ai_response)

        # Señal de grabación de voz
        self.voice_recorder.recording_finished.connect(self._on_voice_recording_finished)

    def _on_state_changed(self, new_state: RobotState):
        """Maneja el cambio de estado emocional."""
        self.ai_widget.update_responses(new_state)
    
    def _insert_ai_response(self, response: str):
        """Inserta una respuesta de IA en el editor. """
        self.response_edit.setText(response)
        logger.debug(f"Respuesta de IA insertada: {response[:50]}...")

    def _on_voice_recording_finished(self, audio_data: bytes):
        """Maneja la finalización de la grabación de voz."""
        try:
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
        
        except Exception as e:
            logger.error(f"Error al enviar datos de voz: {e}")

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
    
    def _clear_response(self):
        """Limpia el contenido del editor."""
        self.response_edit.clear()
        logger.debug("Respuesta limpiada")
    
    def get_response(self) -> str:
        """Obtiene la respuesta editada."""
        return self.response_edit.toPlainText().strip()
    
    def get_state(self) -> RobotState:
        """Obtiene el estado seleccionado."""
        return self.state_widget.get_selected_state()
    
    def accept(self):
        """Maneja la aceptación del diálogo."""
        response = self.get_response()
        state = self.get_state()
        
        if not response:
            # Mostrar advertencia si no hay respuesta
            self.response_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 3px;
                    padding: 10px;
                    font-size: 13px;
                    line-height: 1.4;
                }
            """)
            return
        
        # Emitir señal con los datos
        self.finished.emit(True, response, state.value)
        
        logger.info(f"Respuesta aceptada: {response[:50]}... (Estado: {state.value})")
        super().accept()
    
    def reject(self):
        """Maneja la cancelación del diálogo."""
        self.finished.emit(False, '', '')
        logger.debug("Respuesta cancelada")
        super().reject()
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        self.finished.emit(False, '', '')
        event.accept()
        super().closeEvent(event)
    
    def set_response(self, response: str):
        """
        Establece la respuesta en el editor.
        
        Args:
            response: Nueva respuesta
        """
        self.response_edit.setText(response)
    
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

        self.current_state = state
        self.state_widget.set_selected_state(state)
        self.ai_widget.update_responses(state)
    
    def focus_response_editor(self):
        """Pone el foco en el editor de respuesta."""
        self.response_edit.setFocus()
        self.response_edit.selectAll()

class AIResponseWidget(QDialog):
    """
    Widget para mostrar respuestas generadas por IA.
    Permite al usuario editar y validar la respuesta antes de enviarla.
    """
    
    responseSelected = pyqtSignal(str)

    def __init__(self, response: str, current_state: RobotState = RobotState.ATTENTION, ai_responses: Dict[str, Dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)

        if isinstance(current_state, str):
            try:
                current_state = RobotState(current_state)
            except ValueError:
                current_state = RobotState.ATTENTION

        self.current_state = current_state
        self.ai_responses = ai_responses or {}

        self.setStyleSheet("""
            QFrame{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Título
        title = QLabel("Respuesta Generada por SHARA")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # ComboBox para respuestas
        self.response_combo = QComboBox()
        self.response_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)

        self.response_combo.currentTextChanged.connect(self._on_response_selected)
        layout.addWidget(self.response_combo)

        # Actualizar respuestas para el estado actual
        self.update_responses(current_state)

    def update_responses(self, state: RobotState):
        """Actualiza las respuestas disponibles para un estado."""
        if isinstance(state, str):
            try:
                state = RobotState(state)
            except ValueError:
                state = RobotState.ATTENTION

        self.current_state = state
        self.response_combo.clear()

        # Agregar opción por defecto
        self.response_combo.addItem("-- Selecciona una respuesta generada --")

        # Agregar respuesta para el estado actual si existe
        state_key = state.value
        if state_key in self.ai_responses:
            response_text = self.ai_responses[state_key].get('text', '')
            if response_text:
                # Mostrar preview truncado en el combo
                preview = response_text[:80] + "..." if len(response_text) > 80 else response_text
                self.response_combo.addItem(f"[{state.value}] {preview}")
                # Guardar el texto completo para recuperar después
                self.response_combo.setItemData(1, response_text)
        
        # Agregar respuestas de otros estados
        for other_state_key, response_data in self.ai_responses.items():
            if other_state_key != state_key:
                response_text = response_data.get('text', '')
                if response_text:
                    try:
                        other_state = RobotState(other_state_key)
                        preview = response_text[:80] + "..." if len(response_text) > 80 else response_text
                        display_text = f"[{other_state.value}] {preview}"
                        self.response_combo.addItem(display_text)
                        # Guardar el texto completo
                        current_index = self.response_combo.count() - 1
                        self.response_combo.setItemData(current_index, response_text)
                    except ValueError:
                        continue

    def set_ai_responses(self, ai_responses: Dict[str, Dict]):
        """Establece las respuestas generadas por IA."""
        self.ai_responses = ai_responses
        self.update_responses(self.current_state)

    def _on_response_selected(self, text: str):
        """Maneja la selección de respuesta."""
        if text and text != "-- Selecciona una respuesta generada --":
            # Obtener el texto completo asociado al índice seleccionado
            current_index = self.response_combo.currentIndex()
            full_response = self.response_combo.itemData(current_index)
            if full_response:
                self.responseSelected.emit(full_response)