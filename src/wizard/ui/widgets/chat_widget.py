"""
Widget de chat para SHARA Wizard
"""

import asyncio
from typing import Optional, List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QScrollArea, QButtonGroup,
                            QFrame, QLabel, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QPainter, QColor

from config import RobotState, OperationMode, CHAT_CONFIG
from core.event_manager import EventManager
from services import MessageService, StateService
from models import Message, User
from ui.dialogs.response_dialog import ResponseDialog
from ui.widgets.status_bar import StatusIndicator
from utils.logger import get_logger

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

class AnimatedToggle(QCheckBox):
    """Toggle animado personalizado con slider."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._circle_position = 3
        
        # Animación
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
        
        self.stateChanged.connect(self.on_state_changed)
    
    @pyqtProperty(int)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    def on_state_changed(self, state):
        """Anima el toggle cuando cambia de estado."""
        if state == Qt.CheckState.Checked.value:
            # Mover a la derecha
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(self.width() - 27)
        else:
            # Mover a la izquierda
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(3)
        self.animation.start()
    
    def paintEvent(self, event):
        """Dibuja el toggle personalizado."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar fondo
        if self.isChecked():
            # Verde cuando está activo (Automático)
            bg_color = QColor("#27ae60")
        else:
            # Gris cuando está inactivo (Manual)
            bg_color = QColor("#95a5a6")
        
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
        
        # Dibujar círculo (slider)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(int(self._circle_position), 3, 24, 24)

    def mousePressEvent(self, event):
        """ 
        Maneja los clics del mouse en toda el área del toggle.
        Sobreescribe el comportamiento predeterminado de QCheckBox para permitir clics en cualquier parte del widget.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())
            event.accept()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        """Efecto hover."""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Restaurar cursor."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

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

        emoji = STATE_EMOJIS.get(state, "❓")
        super().__init__(emoji, parent)

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
                font-size: 32px;
                color: #2c3e50;
            }
            QPushButton:checked {
                background-color: #2c3e50;
                color: white;
                border: 2px solid #2c3e50;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border: 2px solid #3498db;
                color: #2c3e50;
            }
            QPushButton:checked:hover {
                background-color: #34495e;
                color: white;
            }
            QToolTip {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #dcdcdc;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
            }
        """)
        
        display_name = STATE_DISPLAY_NAMES.get(state, state.value)
        self.setToolTip(f"🤖 {display_name}")

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
        self.mode_toggle = None
        self.mode_description_label = None
        self.state_buttons = None
        self.status_indicator = None

        # Referencias para animación
        self.input_frame = None
        self.state_buttons_widget = None
        self.input_frame_original_height = 0
        self.state_buttons_original_height = 0
        
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
        
        # Display de chat
        self.chat_display = StyledChatDisplay()
        main_layout.addWidget(self.chat_display)
        
        # Área de input
        self._setup_input_area(main_layout)
        
        # Controles de estado y modo
        self._setup_controls(main_layout)

        # Guardar alturas originales después de que los widgets estén creados
        QTimer.singleShot(100, self._save_original_heights)
        
        logger.debug("UI del chat configurada")

    def _save_original_heights(self):
        """Guarda las alturas originales de los widgets para animaciones."""
        if self.input_frame:
            self.input_frame_original_height = self.input_frame.sizeHint().height()
        if self.state_buttons_widget:
            self.state_buttons_original_height = self.state_buttons_widget.sizeHint().height()

        logger.debug(f"Alturas originales guardadas: input_frame={self.input_frame_original_height}, state_buttons={self.state_buttons_original_height}")

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
        
        # Botones de estado emocional en un widget separado para animar
        self.state_buttons_widget = QWidget()
        state_buttons_layout = QVBoxLayout(self.state_buttons_widget)
        state_buttons_layout.setContentsMargins(0, 0, 0, 0)

        states = list(RobotState)
        self.state_buttons = StateButtonGroup(states)
        state_buttons_layout.addWidget(self.state_buttons)
        
        controls_layout.addWidget(self.state_buttons_widget)
        
        # Toggle de modo
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)

        self.mode_toggle = AnimatedToggle()
        self.mode_toggle.stateChanged.connect(self._on_toggle_changed)
        mode_layout.addWidget(self.mode_toggle)
        
        # Label "Modo Automático"
        mode_label = QLabel("Modo Automático")
        mode_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
            }
        """)
        mode_layout.addWidget(mode_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #bdc9c7;")
        mode_layout.addWidget(separator)

        self.mode_description_label = QLabel("El Operador toma las decisiones")
        self.mode_description_label.setStyleSheet("""
            QLabel {
                color: #2980b9;
                font-size: 12px;
                font-style: italic;
                padding: 5px;
            }
        """)
        mode_layout.addWidget(self.mode_description_label, 1)

        controls_layout.addLayout(mode_layout)
        parent_layout.addWidget(controls_frame)

    def _animate_controls_visibility(self, show: bool):
        """Anima la visibilidad de los controles (input y botones de estado)."""
        
        # Crear grupo de animaciones paralelas
        animation_group = QParallelAnimationGroup(self)
        
        # Animación para input_frame
        if self.input_frame:
            input_animation = QPropertyAnimation(self.input_frame, b"maximumHeight")
            input_animation.setDuration(300)
            input_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            
            if show:
                # Mostrar: de 0 a altura original
                input_animation.setStartValue(0)
                input_animation.setEndValue(self.input_frame_original_height)
                self.input_frame.show()
            else:
                # Ocultar: de altura actual a 0
                input_animation.setStartValue(self.input_frame.height())
                input_animation.setEndValue(0)
            
            animation_group.addAnimation(input_animation)
        
        # Animación para state_buttons_widget
        if self.state_buttons_widget:
            state_animation = QPropertyAnimation(self.state_buttons_widget, b"maximumHeight")
            state_animation.setDuration(300)
            state_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            
            if show:
                # Mostrar: de 0 a altura original
                state_animation.setStartValue(0)
                state_animation.setEndValue(self.state_buttons_original_height)
                self.state_buttons_widget.show()
            else:
                # Ocultar: de altura actual a 0
                state_animation.setStartValue(self.state_buttons_widget.height())
                state_animation.setEndValue(0)
            
            animation_group.addAnimation(state_animation)
        
        if not show:
            animation_group.finished.connect(lambda: self._hide_controls_after_animation())
        
        animation_group.start()
        
        logger.debug(f"Animación de controles iniciada: {'mostrar' if show else 'ocultar'}")
    
    def _connect_signals(self):
        """Conecta las señales del widget."""
        # Suscribirse a eventos
        self.event_manager.subscribe('message_received', self._on_message_received)
        self.event_manager.subscribe('robot_message_received', self._on_robot_message)
        self.event_manager.subscribe('wizard_message_received', self._on_wizard_message)

        # Conectar señales Qt del meessage_service
        self.message_service.message_sent.connect(self._on_message_sent)
        self.message_service.user_response_required.connect(self.show_response_dialog_with_states)

        self.state_service.operation_mode_changed.connect(self._on_mode_changed_internal)
        
        logger.debug("Señales del chat conectadas")

    def _hide_controls_after_animation(self):
        """Oculta los controles después de la animación."""
        if self.input_frame:
            self.input_frame.hide()
        if self.state_buttons_widget:
            self.state_buttons_widget.hide()
    
    def _on_toggle_changed(self, state: int):
        """Maneja cambios en el toggle de modo."""
        new_mode = (OperationMode.AUTOMATIC if state == Qt.CheckState.Checked.value else OperationMode.MANUAL)
        self.state_service.set_operation_mode(new_mode)

    def _on_mode_changed_internal(self, mode: OperationMode):
        """Maneja cambios de modo internamente (solo habilita/deshabilita controles)."""
        # Actualizar toggle sin emitir señal
        self.mode_toggle.blockSignals(True)
        self.mode_toggle.setChecked(mode == OperationMode.AUTOMATIC)
        self.mode_toggle.blockSignals(False)

        # Actualizar descripción y animar controles
        if mode == OperationMode.AUTOMATIC:
            self.mode_description_label.setText("El Robot toma las decisiones")
            self.mode_description_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-size: 12px;
                    font-style: italic;
                    padding: 5px;
                }
            """)
            
            # Ocultar controles con animación
            self._animate_controls_visibility(False)
        else:
            self.mode_description_label.setText("El Operador toma las decisiones")
            self.mode_description_label.setStyleSheet("""
                QLabel {
                    color: #2980b9;
                    font-size: 12px;
                    font-style: italic;
                    padding: 5px;
                }
            """)

            self._animate_controls_visibility(True)

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
        self.active_dialog.adjustSize()
        self.active_dialog.show()

    def show_response_dialog_with_states(self, message: Message, ai_responses: dict = None, user_message: str = ""):
        """
        Muestra el diálogo de respuesta con estados emocionales.
        """
        if not isinstance(ai_responses, dict):
            ai_responses = {}
            
        state = message.robot_state.value if message.robot_state else 'attention'
        self.show_response_dialog(message, state, ai_responses)
    
    def _handle_dialog_response(self, accepted: bool, response: str, state: str):
        """
        Maneja la respuesta del diálogo.
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
        self._on_mode_changed_internal(mode)
    
    def update_connection_status(self, connected: bool):
        """Actualiza el estado de conexión desde la ventana principal."""
        self.is_connected = connected
    
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