"""
Diálogo de respuesta para SHARA Wizard
"""

from typing import Optional, Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QComboBox, QGroupBox, 
                            QButtonGroup, QScrollArea, QFrame, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import RobotState, PRESET_RESPONSES
from utils.logger import get_logger

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
        
        # Agregar respuestas para el estado
        if state in PRESET_RESPONSES:
            for response in PRESET_RESPONSES[state]:
                self.response_combo.addItem(response)
    
    def _on_response_selected(self, text: str):
        """Maneja la selección de respuesta."""
        if text and text != "-- Selecciona una respuesta predefinida --":
            self.responseSelected.emit(text)

class ResponseDialog(QDialog):
    """
    Diálogo para editar y validar respuestas del robot antes de enviarlas.
    """
    
    finished = pyqtSignal(bool, str, str)  # accepted, response, state
    
    def __init__(self, response: str, current_state: RobotState = RobotState.ATTENTION,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.response = response
        self.current_state = current_state
        
        # Componentes
        self.response_edit = None
        self.state_widget = None
        self.preset_widget = None
        
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
        self.preset_widget = PresetResponseWidget(self.current_state)
        layout.addWidget(self.preset_widget)
        
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
        self.state_widget.stateChanged.connect(self.preset_widget.update_responses)
        
        # Insertar respuesta predefinida en el editor
        self.preset_widget.responseSelected.connect(self._insert_preset_response)
    
    def _insert_preset_response(self, response: str):
        """
        Inserta una respuesta predefinida en el editor.
        
        Args:
            response: Respuesta a insertar
        """
        self.response_edit.setText(response)
        logger.debug(f"Respuesta predefinida insertada: {response[:50]}...")
    
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
        self.current_state = state
        self.state_widget.set_selected_state(state)
        self.preset_widget.update_responses(state)
    
    def focus_response_editor(self):
        """Pone el foco en el editor de respuesta."""
        self.response_edit.setFocus()
        self.response_edit.selectAll()