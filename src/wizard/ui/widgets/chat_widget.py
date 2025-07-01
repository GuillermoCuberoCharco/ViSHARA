"""
Widget de chat para SHARA Wizard
"""

import asyncio
from typing import Optional, List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QScrollArea, QButtonGroup,
                            QFrame, QLabel, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from config import RobotState, OperationMode, CHAT_CONFIG
from core.event_manager import EventManager
from services import MessageService, StateService
from models import Message, User
from ui.dialogs.response_dialog import ResponseDialog
from ui.widgets.status_bar import StatusIndicator
from utils.logger import get_logger

logger = get_logger(__name__)

STATE_DISPLAY_NAMES = {
    RobotState.ATTENTION: "Atención",
    RobotState.HELLO: "Saludo", 
    RobotState.ANGRY: "Enfadada",
    RobotState.SAD: "Triste",
    RobotState.JOY: "Feliz",
    RobotState.YES: "Asentir",
    RobotState.NO: "Negativa",
    RobotState.BLUSH: "Sonrojada"
}

class StyledChatDisplay(QTextEdit):
    """Display de chat con estilos personalizados."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                padding: 10px;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
    
    def append_message(self, message: Message):
        """
        Agrega un mensaje con formato específico.
        
        Args:
            message: Mensaje a agregar
        """
        # Colores por tipo de remitente
        color_map = {
            'client': '#2980b9',
            'robot': '#27ae60',
            'wizard': '#8e44ad',
            'system': '#7f8c8d'
        }
        
        sender_name = message.get_sender_display_name()
        color = color_map.get(message.sender.value, '#7f8c8d')
        sender_type = message.sender.value
        
        # Usar tabla para alineación compatible con QTextEdit
        if sender_type == 'client':
            # Mensajes del usuario a la izquierda
            formatted_text = f'''
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 5px 0;">
                <tr>
                    <td width="70%" valign="top">
                        <div style="
                            background-color: #e3f2fd;
                            border-radius: 15px;
                            padding: 8px 12px;
                            margin-right: 20px;
                            border: 1px solid #bbdefb;
                        ">
                            <div style="font-size: 11px; color: {color}; font-weight: bold; margin-bottom: 2px;">
                                {sender_name}
                            </div>
                            <div style="color: #1976d2; line-height: 1.4;">
                                {message.text}
                            </div>
                        </div>
                    </td>
                    <td width="30%"></td>
                </tr>
            </table>
            '''
        elif sender_type in ['wizard', 'robot']:
            # Mensajes del operador/robot a la derecha
            bubble_color = '#f3e5f5' if sender_type == 'wizard' else '#e8f5e8'
            text_color = '#7b1fa2' if sender_type == 'wizard' else '#388e3c'
            border_color = '#e1bee7' if sender_type == 'wizard' else '#c8e6c9'
            
            formatted_text = f'''
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 5px 0;">
                <tr>
                    <td width="30%"></td>
                    <td width="70%" valign="top">
                        <div style="
                            background-color: {bubble_color};
                            border-radius: 15px;
                            padding: 8px 12px;
                            margin-left: 20px;
                            border: 1px solid {border_color};
                        ">
                            <div style="font-size: 11px; color: {color}; font-weight: bold; margin-bottom: 2px;">
                                {sender_name}
                            </div>
                            <div style="color: {text_color}; line-height: 1.4;">
                                {message.text}
                            </div>
                        </div>
                    </td>
                </tr>
            </table>
            '''
        else:
            # Mensajes del sistema centrados
            formatted_text = f'''
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 5px 0;">
                <tr>
                    <td width="15%"></td>
                    <td width="70%" align="center" valign="top">
                        <div style="
                            background-color: #f5f5f5;
                            border-radius: 12px;
                            padding: 6px 10px;
                            color: #616161;
                            font-style: italic;
                            font-size: 12px;
                            border: 1px solid #e0e0e0;
                        ">
                            <div style="font-size: 11px; color: {color}; font-weight: bold; margin-bottom: 2px;">
                                {sender_name}
                            </div>
                            <div style="color: #616161;">
                                {message.text}
                            </div>
                        </div>
                    </td>
                    <td width="15%"></td>
                </tr>
            </table>
            '''
        
        self.append(formatted_text)

class StateButton(QPushButton):
    """Botón para estados emocionales del robot."""
    
    def __init__(self, state: RobotState, parent: Optional[QWidget] = None):

        display_name = STATE_DISPLAY_NAMES.get(state, state.value)
        super().__init__(display_name, parent)

        self.state = state
        self.setCheckable(True)
        self.setFixedSize(100, 70)
        
        # Aplicar estilos
        self.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                margin: 2px;
                font-size: 10px;
            }
            QPushButton:checked {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #2c3e50;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:checked:hover {
                background-color: #34495e;
            }
        """)
        
        self.setToolTip(f"{display_name} ({self.state.value})")

class StateButtonGroup(QWidget):
    """Grupo de botones para selección de estado emocional."""
    
    def __init__(self, states: List[RobotState], parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Crear botones para cada estado
        for state in states:
            button = StateButton(state)
            self.layout.addWidget(button)
            self.button_group.addButton(button)
        
        # Seleccionar el primer estado por defecto
        if states:
            self.button_group.buttons()[0].setChecked(True)
    
    def get_current_state(self) -> Optional[RobotState]:
        """
        Obtiene el estado actualmente seleccionado.
        
        Returns:
            Estado seleccionado o None
        """
        checked_button = self.button_group.checkedButton()
        return checked_button.state if checked_button else None
    
    def set_current_state(self, state: RobotState):
        """
        Establece el estado seleccionado.
        
        Args:
            state: Estado a seleccionar
        """
        for button in self.button_group.buttons():
            if button.state == state:
                button.setChecked(True)
                break

class ChatWidget(QWidget):
    """
    Widget principal de chat que incluye display, input y controles.
    """
    
    def __init__(self, event_manager: EventManager, message_service: MessageService,
                 state_service: StateService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.event_manager = event_manager
        self.message_service = message_service
        self.state_service = state_service
        
        # Estado del widget
        self.current_user: Optional[User] = None
        self.is_connected = False
        self.active_dialog: Optional[ResponseDialog] = None
        
        # Componentes UI
        self.chat_display = None
        self.message_input = None
        self.send_button = None
        self.mode_button = None
        self.state_buttons = None
        self.status_indicator = None
        
        # Timer para keep-alive
        self.keepalive_timer = QTimer()
        self.keepalive_timer.timeout.connect(self._send_keepalive)
        
        self._setup_ui()
        self._connect_signals()
        self._start_keepalive()
        
        logger.debug("ChatWidget inicializado")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario del chat."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Barra de estado del chat
        self._setup_status_bar(main_layout)
        
        # Display de chat
        self.chat_display = StyledChatDisplay()
        main_layout.addWidget(self.chat_display)
        
        # Área de input
        self._setup_input_area(main_layout)
        
        # Controles de estado y modo
        self._setup_controls(main_layout)
        
        logger.debug("UI del chat configurada")
    
    def _setup_status_bar(self, parent_layout):
        """Configura la barra de estado del chat."""
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 5px;")
        status_layout = QHBoxLayout(status_frame)
        
        # Indicador de conexión
        self.connection_label = QLabel("Desconectado")
        self.connection_label.setStyleSheet("color: #e74c3c;")
        status_layout.addWidget(self.connection_label)
        
        # Indicador de modo
        self.mode_label = QLabel("Modo Manual")
        self.mode_label.setStyleSheet("color: #2980b9;")
        status_layout.addWidget(self.mode_label)
        
        parent_layout.addWidget(status_frame)
    
    def _setup_input_area(self, parent_layout):
        """Configura el área de input de mensajes."""
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 5px;")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(5)
        
        # Input de mensaje
        message_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Escribe tu mensaje aquí...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.message_input.returnPressed.connect(self._send_message)
        message_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Enviar")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.send_button.clicked.connect(self._send_message)
        message_layout.addWidget(self.send_button)
        
        input_layout.addLayout(message_layout)
        parent_layout.addWidget(input_frame)
    
    def _setup_controls(self, parent_layout):
        """Configura los controles de estado y modo."""
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 5px;")
        controls_layout = QVBoxLayout(controls_frame)
        
        # Botones de estado emocional
        states = list(RobotState)
        self.state_buttons = StateButtonGroup(states)
        controls_layout.addWidget(self.state_buttons)
        
        # Botón de modo
        button_layout = QHBoxLayout()
        self.mode_button = QPushButton("Modo Auto")
        self.mode_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.mode_button.clicked.connect(self._toggle_mode)
        button_layout.addWidget(self.mode_button)
        
        controls_layout.addLayout(button_layout)
        parent_layout.addWidget(controls_frame)
    
    def _connect_signals(self):
        """Conecta las señales del widget."""
        # Suscribirse a eventos
        self.event_manager.subscribe('message_received', self._on_message_received)
        self.event_manager.subscribe('robot_message_received', self._on_robot_message)
        self.event_manager.subscribe('wizard_message_received', self._on_wizard_message)

        # Conectar señales Qt del meessage_service
        self.message_service.message_sent.connect(self._on_message_sent)
        self.message_service.user_response_required.connect(self.show_response_dialog_with_states)
        
        # Conectar señales de servicios
        self.state_service.operation_mode_changed.connect(self._update_mode_display)
        self.state_service.connection_state_changed.connect(self._update_connection_display)
        
        logger.debug("Señales del chat conectadas")
    
    def _start_keepalive(self):
        """Inicia el timer de keep-alive."""
        self.keepalive_timer.start(CHAT_CONFIG['KEEPALIVE_INTERVAL'] * 1000)
    
    @pyqtSlot()
    def _send_message(self):
        """Envía un mensaje del wizard."""
        text = self.message_input.text().strip()
        if not text:
            return
        
        state = self.state_buttons.get_current_state() or RobotState.ATTENTION
        
        # Crear tarea asíncrona
        asyncio.create_task(self._send_message_async(text, state))
        
        # Limpiar input
        self.message_input.clear()
    
    async def _send_message_async(self, text: str, state: RobotState):
        """
        Envía un mensaje de forma asíncrona.
        
        Args:
            text: Texto del mensaje
            state: Estado emocional
        """
        try:
            success = await self.message_service.send_wizard_message(text, state)
            
            if success:
                logger.debug(f"Mensaje enviado: {text[:50]}...")
            else:
                self._add_error_message("Error al enviar mensaje")
        
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            self._add_error_message(f"Error: {str(e)}")
    
    def _toggle_mode(self):
        """Cambia entre modo manual y automático."""
        current_mode = self.state_service.operation_mode
        new_mode = (OperationMode.AUTOMATIC if current_mode == OperationMode.MANUAL 
                   else OperationMode.MANUAL)
        
        self.state_service.set_operation_mode(new_mode)
    
    def _update_mode_display(self, mode: OperationMode):
        """
        Actualiza la visualización del modo.
        
        Args:
            mode: Nuevo modo de operación
        """
        if mode == OperationMode.AUTOMATIC:
            self.mode_button.setText('Modo Manual')
            self.mode_label.setText('Modo Automático')
            self.mode_label.setStyleSheet("color: #27ae60;")
            
            # Deshabilitar controles en modo automático
            self.message_input.setEnabled(False)
            self.state_buttons.setEnabled(False)
            self.send_button.setEnabled(False)
        else:
            self.mode_button.setText('Modo Auto')
            self.mode_label.setText('Modo Manual')
            self.mode_label.setStyleSheet("color: #2980b9;")
            
            # Habilitar controles en modo manual
            self.message_input.setEnabled(True)
            self.state_buttons.setEnabled(True)
            self.send_button.setEnabled(True)
    
    def _update_connection_display(self, connected: bool):
        """
        Actualiza la visualización de conexión.
        
        Args:
            connected: Estado de conexión
        """
        if connected:
            self.connection_label.setText("Conectado")
            self.connection_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.connection_label.setText("Desconectado")
            self.connection_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def _on_message_received(self, message):
        """Maneja mensajes recibidos."""
        if isinstance(message, Message):
            self.chat_display.append_message(message)
        else:
            # Mensaje genérico
            self._add_system_message(f"Mensaje recibido: {str(message)}")

    def _on_message_sent(self, message: Message):
        """Maneja mensajes enviados."""
        try:
            if message.sender.value == 'wizard':
                current_mode = self.state_service.operation_mode
                if current_mode == OperationMode.AUTOMATIC:
                    display_message = Message.create_robot_message(
                        text=message.text,
                        robot_state=message.robot_state,
                        user_id=message.user_id
                    )
                    mode_text = "Robot"
                else:
                    display_message = message
                    mode_text = "Operador"

                self.chat_display.append_message(display_message)
            
                if message.robot_state:
                    self._add_state_message(f"{mode_text} state: {message.robot_state.value}")

        except Exception as e:
            logger.error(f"Error procesando mensaje enviado: {e}")
    
    def _on_robot_message(self, message: Message):
        """Maneja mensajes del robot."""
        self.chat_display.append_message(message)
    
    def _on_wizard_message(self, message: Message):
        """Maneja mensajes del wizard."""
        self.chat_display.append_message(message)

        if message.robot_state:
            self._add_state_message(f"Robot state: {message.robot_state.value}")
    
    def _add_system_message(self, text: str):
        """Agrega un mensaje del sistema."""
        self.chat_display.append(
            f'''<table width="100%" cellpadding="0" cellspacing="0" style="margin: 5px 0;">
                <tr>
                    <td width="15%"></td>
                    <td width="70%" align="center">
                        <div style="
                            background-color: #f0f0f0;
                            border-radius: 12px;
                            padding: 6px 10px;
                            color: #7f8c8d;
                            font-style: italic;
                            font-size: 12px;
                            border: 1px solid #e0e0e0;
                        ">{text}</div>
                    </td>
                    <td width="15%"></td>
                </tr>
            </table>'''
        )

    def _add_state_message(self, text: str):
        """Agrega un mensaje de estado."""
        self.chat_display.append(
            f'''<table width="100%" cellpadding="0" cellspacing="0" style="margin: 5px 0;">
                <tr>
                    <td width="15%"></td>
                    <td width="70%" align="center">
                        <div style="
                            background-color: #fff3e0;
                            border-radius: 12px;
                            padding: 6px 10px;
                            color: #e67e22;
                            font-size: 12px;
                            border: 1px solid #ffcc80;
                        ">{text}</div>
                    </td>
                    <td width="15%"></td>
                </tr>
            </table>'''
        )

    def _add_error_message(self, text: str):
        """Agrega un mensaje de error."""
        self.chat_display.append(
            f'''<table width="100%" cellpadding="0" cellspacing="0" style="margin: 5px 0;">
                <tr>
                    <td width="15%"></td>
                    <td width="70%" align="center">
                        <div style="
                            background-color: #ffebee;
                            border-radius: 12px;
                            padding: 6px 10px;
                            color: #e74c3c;
                            font-weight: bold;
                            font-size: 12px;
                            border: 1px solid #ffcdd2;
                        ">ERROR: {text}</div>
                    </td>
                    <td width="15%"></td>
                </tr>
            </table>'''
        )
    
    def _send_keepalive(self):
        """Envía señal de keep-alive."""
        # Implementar keep-alive si es necesario
        pass
    
    def show_response_dialog(self, message: Message, state: str, ai_response: dict = None):
        """
        Muestra el diálogo de respuesta.
        
        Args:
            message: Mensaje que requiere respuesta
            state: Estado emocional actual
            ai_response: Respuesta de IA opcional con presets
        """
        if self.active_dialog:
            self.active_dialog.close()
        
        try:
            # Validar y normalizar el parámetro state
            if isinstance(state, str):
                current_state = RobotState(state)
            elif isinstance(state, RobotState):
                current_state = state
            elif isinstance(state, dict):
                # Extraer el estado del mensaje y usar el dict como ai_response
                current_state = message.robot_state if message.robot_state else RobotState.ATTENTION
                if ai_response is None:
                    ai_response = state
                logger.warning(f"Se recibió diccionario como state, usando estado del mensaje: {current_state.value}")
            else:
                logger.warning(f"Tipo de state no válido: {type(state)}, usando ATTENTION por defecto")
                current_state = RobotState.ATTENTION
                
        except ValueError:
            logger.warning(f"Estado inválido: {state}, usando ATTENTION por defecto")
            current_state = RobotState.ATTENTION
        
        self.active_dialog = ResponseDialog(
            message.text, 
            current_state,
            ai_response or {},
            self
        )

        self.active_dialog.finished.connect(self._handle_dialog_response)
        self.active_dialog.show()

    def show_response_dialog_with_states(self, message: Message, ai_responses: dict = None, user_message: str = ""):
        """
        Muestra el diálogo de respuesta con estados emocionales.
        
        Args:
            message: Mensaje que requiere respuesta
            ai_response: Respuesta de IA opcional con presets
            user_message: Mensaje original del usuario
        """
        if not isinstance(ai_responses, dict):
            logger.warning(f"ai_responses no es un diccionario: {type(ai_responses)}, usando diccionario vacío")
            ai_responses = {}
            
        state = message.robot_state.value if message.robot_state else 'attention'
        self.show_response_dialog(message, state, ai_responses)
    
    def _handle_dialog_response(self, accepted: bool, response: str, state: str):
        """
        Maneja la respuesta del diálogo.
        
        Args:
            accepted: Si se aceptó la respuesta
            response: Texto de respuesta
            state: Estado emocional
        """
        self.active_dialog = None
        
        if accepted and response.strip():
            try:
                robot_state = RobotState(state)
                asyncio.create_task(self._send_message_async(response, robot_state))
            except ValueError:
                logger.error(f"Estado inválido: {state}")
    
    # Métodos públicos para la ventana principal
    def update_mode(self, mode: OperationMode):
        """Actualiza el modo desde la ventana principal."""
        self._update_mode_display(mode)
    
    def update_connection_status(self, connected: bool):
        """Actualiza el estado de conexión desde la ventana principal."""
        self.is_connected = connected
        self._update_connection_display(connected)
    
    def update_current_user(self, user: Optional[User]):
        """Actualiza el usuario actual."""
        self.current_user = user
        
        if user:
            self._add_system_message(f"Usuario actual: {user.get_display_name()}")
        else:
            self._add_system_message("Usuario desconectado")
    
    async def cleanup(self):
        """Limpia recursos del widget."""
        try:
            logger.info("Limpiando widget de chat...")
            
            # Detener timer
            self.keepalive_timer.stop()
            
            # Cerrar diálogo activo
            if self.active_dialog:
                self.active_dialog.close()
            
            logger.info("Widget de chat limpiado")
            
        except Exception as e:
            logger.error(f"Error limpiando widget de chat: {e}")
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del widget.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'is_connected': self.is_connected,
            'current_user_id': self.current_user.user_id if self.current_user else None,
            'operation_mode': self.state_service.operation_mode.value,
            'has_active_dialog': self.active_dialog is not None,
            'selected_state': self.state_buttons.get_current_state().value if self.state_buttons.get_current_state() else None
        }